from decimal import Decimal
import uuid

from django.db import transaction
from django.utils import timezone

from finance.models import FinancePayment, PaymentStatus
from finance.services import initiate_refund, settle_payment_and_allocate
from payments.exceptions import record_payment_exception
from payments.models import (
    GatewayEvent,
    GatewayEventStatus,
    GatewayIntentStatus,
    PaymentIntentRecord,
    ProviderDispute,
    SavedPaymentMethod,
)


class UnmatchedPaymentError(ValueError):
    """Gateway event resolved an intent but no authoritative payment record."""


class SettlementAllocationRequired(ValueError):
    """Settlement cannot be applied to receivables without explicit allocation facts."""


STATUS_MAP = {
    "created": GatewayIntentStatus.CREATED,
    "pending": GatewayIntentStatus.PENDING,
    "authorized": GatewayIntentStatus.AUTHORIZED,
    "settling": GatewayIntentStatus.SETTLING,
    "settled": GatewayIntentStatus.SETTLED,
    "failed": GatewayIntentStatus.FAILED,
    "refunded": GatewayIntentStatus.REFUNDED,
    "canceled": GatewayIntentStatus.CANCELED,
}


def normalize_gateway_status(raw_status: str) -> str:
    if not raw_status:
        return GatewayIntentStatus.PENDING
    return STATUS_MAP.get(raw_status.lower(), GatewayIntentStatus.PENDING)


@transaction.atomic
def process_gateway_event(event: GatewayEvent) -> None:
    payload = event.payload or {}
    event_type = (event.event_type or "").lower()

    if event_type == "payment_method.saved":
        _handle_saved_payment_method(event, payload)
        _mark_processed(event)
        return

    if event_type == "payment_method.detached":
        _handle_detached_payment_method(event, payload)
        _mark_processed(event)
        return

    if event_type == "dispute.opened":
        _handle_dispute_opened(event, payload)
        _mark_processed(event)
        return

    if event_type.startswith("dispute."):
        _handle_dispute_status_update(event, payload)
        _mark_processed(event)
        return

    provider_intent_id = (
        payload.get("intent_id")
        or payload.get("data", {}).get("intent_id")
        or event.provider_intent_id
    )
    provider_payment_id = (
        payload.get("payment_id")
        or payload.get("data", {}).get("payment_id")
        or event.provider_payment_id
    )
    status = normalize_gateway_status(
        payload.get("status")
        or payload.get("data", {}).get("status")
        or ""
    )

    intent = PaymentIntentRecord.objects.filter(
        provider=event.provider,
        provider_intent_id=provider_intent_id,
    ).first()

    if not intent:
        event.status = GatewayEventStatus.IGNORED
        event.error_message = "No matching PaymentIntentRecord found."
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "error_message", "processed_at"])
        return

    intent.provider_payment_id = provider_payment_id or intent.provider_payment_id
    intent.status = status
    intent.response_payload = payload
    intent.save(update_fields=["provider_payment_id", "status", "response_payload", "updated_at"])

    if status == GatewayIntentStatus.SETTLED:
        _apply_settlement(intent, payload)

    if status == GatewayIntentStatus.REFUNDED:
        _apply_refund(intent, payload, provider=event.provider)

    _mark_processed(event)


def _mark_processed(event: GatewayEvent) -> None:
    event.status = GatewayEventStatus.PROCESSED
    event.processed_at = timezone.now()
    event.save(update_fields=["status", "processed_at"])


def _amount(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_uuid_or_none(value):
    if value in (None, ""):
        return None
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


def _find_finance_payment(intent: PaymentIntentRecord) -> FinancePayment | None:
    """
    Resolve the compatibility FinancePayment using explicit identifier ownership.

    The provider payment id is never overloaded with provider intent id or
    client reference id. During migration, callers can supply finance_payment_id
    in intent metadata as the strongest compatibility link.
    """
    finance_payment_id = (intent.metadata or {}).get("finance_payment_id")
    if finance_payment_id:
        payment = FinancePayment.objects.filter(
            pk=finance_payment_id,
            school_id=intent.school_id,
        ).first()
        if payment is not None:
            return payment

    if intent.provider_payment_id:
        return FinancePayment.objects.filter(
            school_id=intent.school_id,
            processor_payment_id=intent.provider_payment_id,
        ).first()

    return None


def _settlement_allocations(intent: PaymentIntentRecord, payload: dict) -> list[dict]:
    """Read explicit allocation facts supplied by the canonical caller/adapter."""
    metadata = intent.metadata or {}
    allocations = metadata.get("allocations")
    if allocations is None:
        allocations = payload.get("allocations")
    if not isinstance(allocations, list) or not allocations:
        raise SettlementAllocationRequired(
            "Settled gateway payment is missing explicit obligation allocations."
        )
    return allocations


def _apply_settlement(intent: PaymentIntentRecord, payload: dict) -> None:
    payment = _find_finance_payment(intent)
    if payment is None:
        raise UnmatchedPaymentError(
            "Settled gateway intent has no matching FinancePayment compatibility record."
        )

    if payment.status == PaymentStatus.SETTLED:
        return

    allocations_payload = _settlement_allocations(intent, payload)
    settle_payment_and_allocate(
        payment=payment,
        allocations_payload=allocations_payload,
    )


def _apply_refund(intent: PaymentIntentRecord, payload: dict, *, provider: str) -> None:
    payment = _find_finance_payment(intent)
    if payment is None:
        raise UnmatchedPaymentError(
            "Refunded gateway intent has no matching FinancePayment compatibility record."
        )

    amount = _amount(payload.get("refund_amount") or payload.get("amount") or intent.amount)
    refund_cents = int((amount * Decimal("100")).quantize(Decimal("1")))

    idem = f"gw_refund:{intent.provider}:{intent.provider_payment_id or intent.provider_intent_id}"
    if payment.refunds.filter(idempotency_key=idem).exists():
        return

    initiate_refund(
        payment=payment,
        amount_cents=max(refund_cents, 1),
        processor=provider,
        created_by=None,
        idempotency_key=idem,
    )


def _handle_saved_payment_method(event: GatewayEvent, payload: dict) -> None:
    metadata = payload.get("metadata") or {}
    school_id = _to_uuid_or_none(metadata.get("school_id") or event.school_id)
    household_id = _to_uuid_or_none(metadata.get("household_id"))
    provider_method_id = payload.get("payment_method_id") or payload.get("method_id")

    if not school_id or not household_id or not provider_method_id:
        raise ValueError("Saved payment method event missing school_id, household_id, or provider method id.")

    SavedPaymentMethod.objects.update_or_create(
        provider_method_id=provider_method_id,
        defaults={
            "school_id": school_id,
            "household_id": household_id,
            "provider": event.provider,
            "provider_customer_id": payload.get("customer_id", ""),
            "method_type": payload.get("method_type", "card"),
            "brand": payload.get("brand", ""),
            "last4": payload.get("last4", ""),
            "exp_month": payload.get("exp_month"),
            "exp_year": payload.get("exp_year"),
            "is_default": bool(payload.get("is_default", False)),
            "is_active": True,
            "payload": payload,
        },
    )


def _handle_detached_payment_method(event: GatewayEvent, payload: dict) -> None:
    provider_method_id = payload.get("payment_method_id") or payload.get("method_id")
    method = SavedPaymentMethod.objects.filter(
        provider_method_id=provider_method_id,
        provider=event.provider,
    ).first()
    if method:
        method.is_active = False
        method.is_default = False
        method.payload = payload
        method.save(update_fields=["is_active", "is_default", "payload", "updated_at"])


def _handle_dispute_opened(event: GatewayEvent, payload: dict) -> None:
    metadata = payload.get("metadata") or {}
    ProviderDispute.objects.update_or_create(
        dispute_id=payload.get("dispute_id") or payload.get("id"),
        defaults={
            "school_id": _to_uuid_or_none(metadata.get("school_id") or event.school_id),
            "provider": event.provider,
            "provider_payment_id": payload.get("payment_id", ""),
            "provider_intent_id": payload.get("intent_id", ""),
            "invoice_id": _to_uuid_or_none(metadata.get("invoice_id")),
            "household_id": _to_uuid_or_none(metadata.get("household_id")),
            "amount": _amount(payload.get("amount")),
            "currency": payload.get("currency") or "USD",
            "reason": payload.get("reason") or "",
            "status": payload.get("status") or "open",
            "payload": payload,
            "opened_at": timezone.now(),
        },
    )


def _handle_dispute_status_update(event: GatewayEvent, payload: dict) -> None:
    dispute = ProviderDispute.objects.filter(
        dispute_id=payload.get("dispute_id") or payload.get("id")
    ).first()
    if not dispute:
        return

    dispute.status = payload.get("status") or dispute.status
    dispute.payload = payload
    if dispute.status in {"won", "lost", "closed"}:
        dispute.closed_at = timezone.now()
    dispute.save(update_fields=["status", "payload", "closed_at", "updated_at"])


def process_gateway_event_safely(event: GatewayEvent) -> None:
    try:
        process_gateway_event(event)
    except Exception as exc:
        event.status = GatewayEventStatus.FAILED
        event.error_message = str(exc)
        event.save(update_fields=["status", "error_message"])

        record_payment_exception(
            school_id=event.school_id,
            provider=event.provider,
            category="gateway_event_processing",
            message=str(exc),
            payload=event.payload or {},
            gateway_event_id=event.id,
        )
        raise
