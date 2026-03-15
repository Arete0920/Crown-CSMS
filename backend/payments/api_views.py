import json
import logging
import uuid
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from finance.models import FinancePayment, PaymentStatus, Processor
from households.scoping import get_request_school_id
from payments.models import (
    GatewayEvent,
    GatewayEventStatus,
    GatewayIntentStatus,
    GatewayProvider,
    PaymentIntentRecord,
)
from payments.providers import get_gateway
from payments.services import process_gateway_event_safely
from payments.webhooks import verify_compuwerx_signature


logger = logging.getLogger(__name__)


def _decimal(value) -> Decimal:
    return Decimal(str(value))


def _to_uuid_or_none(value):
    if value in (None, ""):
        return None
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    school_id = get_request_school_id(request, required=True)

    invoice_id = _to_uuid_or_none(request.data.get("invoice_id"))
    household_id = _to_uuid_or_none(request.data.get("household_id"))

    try:
        amount = _decimal(request.data.get("amount"))
    except Exception:
        return Response({"ok": False, "error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

    if amount <= Decimal("0"):
        return Response({"ok": False, "error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

    currency = request.data.get("currency", "USD")
    description = request.data.get("description", "Crown payment")
    provider = request.data.get("provider", GatewayProvider.COMPUWERX)

    client_reference_id = f"crown-{school_id}-{uuid.uuid4().hex[:20]}"

    amount_cents = int((amount * Decimal("100")).quantize(Decimal("1")))
    finance_payment = FinancePayment.objects.create(
        school_id=school_id,
        payer_user=request.user,
        amount_cents=amount_cents,
        currency=currency,
        processor=Processor.COMPUWERX,
        status=PaymentStatus.PENDING,
        processor_payment_id=client_reference_id,
        idempotency_key=client_reference_id,
        created_by=request.user,
    )

    req_payload = request.data if isinstance(request.data, dict) else dict(request.data)
    metadata = request.data.get("metadata") or {}

    record = PaymentIntentRecord.objects.create(
        school_id=school_id,
        provider=provider,
        invoice_id=invoice_id,
        household_id=household_id,
        amount=amount,
        currency=currency,
        client_reference_id=client_reference_id,
        status=GatewayIntentStatus.CREATED,
        request_payload=req_payload,
        metadata={
            "finance_payment_id": str(finance_payment.id),
            **metadata,
        },
        created_by=request.user,
    )

    gateway = get_gateway(provider)
    result = gateway.create_intent(
        amount=amount,
        currency=currency,
        client_reference_id=client_reference_id,
        description=description,
        metadata={
            "school_id": str(school_id),
            "invoice_id": str(invoice_id) if invoice_id else "",
            "household_id": str(household_id) if household_id else "",
            "finance_payment_id": str(finance_payment.id),
            **metadata,
        },
    )

    if not result.ok:
        record.status = GatewayIntentStatus.FAILED
        record.response_payload = {"error": result.error, "raw": result.raw or {}}
        record.save(update_fields=["status", "response_payload", "updated_at"])
        finance_payment.status = PaymentStatus.FAILED
        finance_payment.save(update_fields=["status", "updated_at"])
        return Response(
            {"ok": False, "error": result.error},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    record.provider_intent_id = result.provider_intent_id
    record.provider_payment_id = result.provider_payment_id
    record.status = result.status or GatewayIntentStatus.PENDING
    record.response_payload = result.raw or {}
    record.save(update_fields=["provider_intent_id", "provider_payment_id", "status", "response_payload", "updated_at"])

    finance_payment.processor_payment_id = result.provider_payment_id or result.provider_intent_id or client_reference_id
    finance_payment.save(update_fields=["processor_payment_id", "updated_at"])

    return Response(
        {
            "ok": True,
            "intent_id": record.provider_intent_id,
            "payment_id": record.provider_payment_id,
            "status": record.status,
            "checkout_url": result.checkout_url,
            "client_reference_id": record.client_reference_id,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_intent_status(request, intent_id: str):
    school_id = get_request_school_id(request, required=True)

    record = PaymentIntentRecord.objects.filter(
        school_id=school_id,
        provider_intent_id=intent_id,
    ).first()

    if not record:
        return Response({"detail": "Payment intent not found."}, status=status.HTTP_404_NOT_FOUND)

    gateway = get_gateway(record.provider)
    result = gateway.fetch_status(provider_intent_id=record.provider_intent_id)

    if result.ok:
        record.status = result.status or record.status
        record.provider_payment_id = result.provider_payment_id or record.provider_payment_id
        record.response_payload = result.raw or {}
        record.save(update_fields=["status", "provider_payment_id", "response_payload", "updated_at"])

    return Response(
        {
            "ok": result.ok,
            "intent_id": record.provider_intent_id,
            "payment_id": record.provider_payment_id,
            "status": record.status,
            "error": result.error,
        }
    )


@csrf_exempt
def compuwerx_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    signature = request.headers.get("X-Compuwerx-Signature", "")
    if not verify_compuwerx_signature(request.body, signature):
        return JsonResponse({"ok": False, "error": "Invalid signature"}, status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    event_id = payload.get("event_id") or payload.get("id")
    if not event_id:
        return JsonResponse({"ok": False, "error": "Missing event_id"}, status=400)

    event_type = payload.get("event_type") or payload.get("type") or "unknown"
    provider_intent_id = payload.get("intent_id") or payload.get("data", {}).get("intent_id", "")
    provider_payment_id = payload.get("payment_id") or payload.get("data", {}).get("payment_id", "")
    school_id = _to_uuid_or_none(
        payload.get("metadata", {}).get("school_id")
        or payload.get("school_id")
    )

    event, created = GatewayEvent.objects.get_or_create(
        provider=GatewayProvider.COMPUWERX,
        event_id=event_id,
        defaults={
            "school_id": school_id,
            "event_type": event_type,
            "provider_intent_id": provider_intent_id,
            "provider_payment_id": provider_payment_id,
            "signature": signature,
            "raw_body": request.body.decode("utf-8"),
            "payload": payload,
        },
    )

    if not created:
        return JsonResponse({"ok": True, "duplicate": True})

    try:
        process_gateway_event_safely(event)
    except Exception:
        logger.exception("compuwerx_webhook: unexpected processing failure", extra={"event_id": event_id})
        return JsonResponse({"ok": False, "error": "Webhook processing failed."}, status=500)

    return JsonResponse({"ok": True})
