from decimal import Decimal
import uuid

from django.db import transaction
from django.utils import timezone

from billing.models import Invoice as BillingInvoice
from finance.models import FinancePayment
from households.models import Household
from payments.authority_services import (
    create_payment,
    request_refund,
    settle_payment,
    settle_refund,
)
from payments.exceptions import record_payment_exception
from payments.models import (
    GatewayEvent,
    GatewayEventStatus,
    GatewayIntentStatus,
    Payment,
    PaymentIntentRecord,
    ProviderDispute,
    SavedPaymentMethod,
)


class UnmatchedPaymentError(ValueError):
    """Gateway event cannot be mapped safely to an owned local record."""


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
    if not isinstance(payload, dict):
        raise UnmatchedPaymentError("Gateway payload must be an object.")
    if event.school_id is None:
        raise UnmatchedPaymentError("Gateway event requires verified school ownership.")
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise UnmatchedPaymentError("Gateway metadata must be an object.")
    claimed_school = metadata.get("school_id")
    if claimed_school not in (None, "") and _to_uuid_or_none(claimed_school) != event.school_id:
        raise UnmatchedPaymentError("Gateway metadata conflicts with verified school ownership.")

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

    if not provider_intent_id:
        raise UnmatchedPaymentError("Gateway event requires a provider intent reference.")

    # The current schema indexes provider_intent_id but does not enforce
    # uniqueness. Never choose an arbitrary school-owned match: settling the
    # wrong record could attribute receivables to another household.
    matching_intents = list(
        PaymentIntentRecord.objects.select_for_update().filter(
            school_id=event.school_id,
            provider=event.provider,
            provider_intent_id=provider_intent_id,
        ).order_by("pk")[:2]
    )
    if len(matching_intents) > 1:
        raise UnmatchedPaymentError("Ambiguous provider intent reference for this school.")
    intent = matching_intents[0] if matching_intents else None

    if not intent:
        event.status = GatewayEventStatus.IGNORED
        event.error_message = "No matching PaymentIntentRecord found."
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "error_message", "processed_at"])
        return

    if provider_payment_id and intent.provider_payment_id and provider_payment_id != intent.provider_payment_id:
        raise UnmatchedPaymentError("Gateway payment reference conflicts with the owned intent.")

    intent.provider_payment_id = provider_payment_id or intent.provider_payment_id
    intent.status = status
    intent.response_payload = payload
    intent.save(update_fields=["provider_payment_id", "status", "response_payload", "updated_at"])

    if status == GatewayIntentStatus.SETTLED:
        _apply_settlement(intent, payload)

    if status == GatewayIntentStatus.REFUNDED:
        _apply_refund(event, intent, payload, provider=event.provider)

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


def _canonical_payment_for_legacy(
    intent: PaymentIntentRecord,
    legacy_payment: FinancePayment,
    *,
    create_if_missing: bool,
) -> Payment | None:
    canonical = Payment.objects.select_for_update().filter(
        school_id=intent.school_id,
        finance_payment_id=legacy_payment.pk,
    ).first()

    if canonical is not None:
        if int(canonical.amount_cents) != int(legacy_payment.amount_cents):
            raise UnmatchedPaymentError(
                "Canonical Payment amount conflicts with FinancePayment compatibility record."
            )
        if (canonical.currency or "USD").upper() != (legacy_payment.currency or "USD").upper():
            raise UnmatchedPaymentError(
                "Canonical Payment currency conflicts with FinancePayment compatibility record."
            )
        if intent.household_id and canonical.household_id != intent.household_id:
            raise UnmatchedPaymentError(
                "Canonical Payment household conflicts with PaymentIntentRecord."
            )
        return canonical

    if not create_if_missing:
        return None

    return create_payment(
        school_id=intent.school_id,
        household_id=intent.household_id,
        finance_payment_id=legacy_payment.pk,
        amount_cents=legacy_payment.amount_cents,
        currency=legacy_payment.currency,
        provider=intent.provider,
        provider_intent_id=intent.provider_intent_id,
        provider_payment_id=intent.provider_payment_id,
        idempotency_key=f"gateway_intent:{intent.pk}",
        metadata={"payment_intent_record_id": intent.pk},
    )


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
    legacy_payment = _find_finance_payment(intent)
    if legacy_payment is None:
        raise UnmatchedPaymentError(
            "Settled gateway intent has no matching FinancePayment compatibility record."
        )

    allocations_payload = _settlement_allocations(intent, payload)
    canonical_payment = _canonical_payment_for_legacy(
        intent,
        legacy_payment,
        create_if_missing=True,
    )
    if canonical_payment is None:  # pragma: no cover - create_if_missing guarantees a Payment
        raise UnmatchedPaymentError("Canonical Payment could not be resolved for settlement.")

    settle_payment(
        payment=canonical_payment,
        allocations_payload=allocations_payload,
        provider=intent.provider,
        provider_intent_id=intent.provider_intent_id,
        provider_payment_id=intent.provider_payment_id,
    )


def _apply_refund(
    event: GatewayEvent,
    intent: PaymentIntentRecord,
    payload: dict,
    *,
    provider: str,
) -> None:
    legacy_payment = _find_finance_payment(intent)
    if legacy_payment is None:
        raise UnmatchedPaymentError(
            "Refunded gateway intent has no matching FinancePayment compatibility record."
        )

    canonical_payment = _canonical_payment_for_legacy(
        intent,
        legacy_payment,
        create_if_missing=False,
    )
    if canonical_payment is None:
        raise UnmatchedPaymentError(
            "Refunded gateway intent has no canonical Payment; settlement reconciliation is required first."
        )

    amount = _amount(payload.get("refund_amount") or payload.get("amount") or intent.amount)
    refund_cents = int((amount * Decimal("100")).quantize(Decimal("1")))
    data = payload.get("data") or {}
    provider_refund_id = str(payload.get("refund_id") or data.get("refund_id") or "").strip()

    refund = request_refund(
        payment=canonical_payment,
        amount_cents=refund_cents,
        provider=provider,
        idempotency_key=f"gateway_refund_event:{event.provider}:{event.event_id}",
        metadata={"gateway_event_id": event.pk},
    )
    settle_refund(
        refund=refund,
        provider=provider,
        provider_refund_id=provider_refund_id,
    )


def _handle_saved_payment_method(event: GatewayEvent, payload: dict) -> None:
    metadata = payload.get("metadata") or {}
    household_id = _to_uuid_or_none(metadata.get("household_id"))
    provider_method_id = payload.get("payment_method_id") or payload.get("method_id")

    if not household_id or not provider_method_id:
        raise UnmatchedPaymentError("Saved payment method event requires household and method references.")
    if not Household.objects.filter(pk=household_id, school_id=event.school_id).exists():
        raise UnmatchedPaymentError("Saved payment method household is not owned by event school.")

    # The provider method identifier is globally unique in the retained schema.
    # A locked get_or_create closes the check/update race with another tenant.
    defaults = {
        "school_id": event.school_id,
        "household_id": household_id,
        "provider": event.provider,
        "provider_customer_id": payload.get("customer_id", ""),
        "method_type": payload.get("method_type", "card"),
        "brand": payload.get("brand", ""),
        "last4": payload.get("last4", ""),
        "exp_month": payload.get("exp_month"),
        "exp_year": payload.get("exp_year"),
        "is_default": bool(payload.get("is_default", False)),
        "payload": payload,
    }
    method, created = SavedPaymentMethod.objects.select_for_update().get_or_create(
        provider_method_id=provider_method_id,
        defaults=defaults,
    )
    if (
        method.school_id != event.school_id
        or method.household_id != household_id
        or method.provider != event.provider
    ):
        raise UnmatchedPaymentError("Saved payment method identifier conflicts with existing ownership.")
    if not created:
        mutable_fields = [key for key in defaults if key not in ("school_id", "household_id", "provider")]
        for field_name in mutable_fields:
            setattr(method, field_name, defaults[field_name])
        method.save(update_fields=[*mutable_fields, "updated_at"])


def _handle_detached_payment_method(event: GatewayEvent, payload: dict) -> None:
    provider_method_id = payload.get("payment_method_id") or payload.get("method_id")
    if not provider_method_id:
        raise UnmatchedPaymentError("Payment method detach event has no provider method reference.")
    # A provider method ID is globally unique in the retained schema.
    # Reject foreign ownership instead of silently marking it processed.
    method = SavedPaymentMethod.objects.select_for_update().filter(
        provider_method_id=provider_method_id,
    ).first()
    if not method:
        return
    if method.school_id != event.school_id or method.provider != event.provider:
        raise UnmatchedPaymentError("Payment method reference conflicts with verified ownership.")
    method.is_active = False
    method.is_default = False
    method.payload = payload
    method.save(update_fields=["is_active", "is_default", "payload", "updated_at"])


def _handle_dispute_opened(event: GatewayEvent, payload: dict) -> None:
    metadata = payload.get("metadata") or {}
    dispute_id = payload.get("dispute_id") or payload.get("id")
    if not dispute_id:
        raise UnmatchedPaymentError("Dispute event has no provider dispute reference.")

    household_id = _to_uuid_or_none(metadata.get("household_id"))
    invoice_id = _to_uuid_or_none(metadata.get("invoice_id"))
    if metadata.get("household_id") and (
        not household_id
        or not Household.objects.filter(pk=household_id, school_id=event.school_id).exists()
    ):
        raise UnmatchedPaymentError("Dispute household is not owned by event school.")
    if metadata.get("invoice_id") and (
        not invoice_id
        or not BillingInvoice.objects.filter(pk=invoice_id, school_id=event.school_id).exists()
    ):
        raise UnmatchedPaymentError("Dispute invoice is not owned by event school.")

    # Reject a trusted provider identifier already bound to another tenant.
    for field, reference in (
        ("provider_intent_id", payload.get("intent_id")),
        ("provider_payment_id", payload.get("payment_id")),
    ):
        if reference and (
            PaymentIntentRecord.objects.filter(
                provider=event.provider, **{field: reference},
            ).exclude(school_id=event.school_id).exists()
            or Payment.objects.filter(
                provider=event.provider, **{field: reference},
            ).exclude(school_id=event.school_id).exists()
        ):
            raise UnmatchedPaymentError("Dispute provider reference belongs to another school.")
    if payload.get("payment_id") and FinancePayment.objects.filter(
        processor=event.provider, processor_payment_id=payload["payment_id"],
    ).exclude(school_id=event.school_id).exists():
        raise UnmatchedPaymentError("Dispute payment reference belongs to another school.")

    defaults = {
        "school_id": event.school_id,
        "provider": event.provider,
        "provider_payment_id": payload.get("payment_id", ""),
        "provider_intent_id": payload.get("intent_id", ""),
        "invoice_id": invoice_id,
        "household_id": household_id,
        "amount": _amount(payload.get("amount")),
        "currency": payload.get("currency") or "USD",
        "reason": payload.get("reason") or "",
        "status": payload.get("status") or "open",
        "payload": payload,
        "opened_at": timezone.now(),
    }
    dispute, created = ProviderDispute.objects.select_for_update().get_or_create(
        dispute_id=dispute_id,
        defaults=defaults,
    )
    if dispute.school_id != event.school_id or dispute.provider != event.provider:
        raise UnmatchedPaymentError("Provider dispute identifier conflicts with existing ownership.")
    if not created:
        mutable_fields = [key for key in defaults if key not in ("school_id", "provider")]
        for field_name in mutable_fields:
            setattr(dispute, field_name, defaults[field_name])
        dispute.save(update_fields=[*mutable_fields, "updated_at"])


def _handle_dispute_status_update(event: GatewayEvent, payload: dict) -> None:
    dispute_id = payload.get("dispute_id") or payload.get("id")
    if not dispute_id:
        raise UnmatchedPaymentError("Dispute update has no provider dispute reference.")
    # The retained dispute ID is globally unique. Do not silently mark a
    # foreign-school or foreign-provider event as processed.
    dispute = ProviderDispute.objects.select_for_update().filter(
        dispute_id=dispute_id,
    ).first()
    if not dispute:
        return
    if dispute.school_id != event.school_id or dispute.provider != event.provider:
        raise UnmatchedPaymentError("Dispute reference conflicts with verified ownership.")

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

        # Unowned events cannot be written to the tenant-required exception ledger.
        # The GatewayEvent itself remains FAILED for investigation.
        if event.school_id is not None:
            record_payment_exception(
                school_id=event.school_id,
                provider=event.provider,
                category="gateway_event_processing",
                message=str(exc),
                payload=event.payload or {},
                gateway_event_id=event.id,
            )
        raise
