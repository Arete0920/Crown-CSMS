from __future__ import annotations

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from finance.models import FinancePayment, PaymentStatus as LegacyPaymentStatus
from finance.services import initiate_refund, settle_payment_and_allocate
from payments.models import (
    CanonicalPaymentStatus,
    CanonicalRefundStatus,
    Payment,
    Refund,
)


class PaymentAuthorityError(ValueError):
    """Base error for canonical Payments authority invariants."""


class IdempotencyConflict(PaymentAuthorityError):
    """An idempotency key or financial replay conflicts with canonical facts."""


class InvalidPaymentState(PaymentAuthorityError):
    """A requested Payment or Refund state transition is not allowed."""


class CanonicalOverRefundError(PaymentAuthorityError):
    """Requested refunds would exceed the original canonical Payment amount."""


class PaymentCompatibilityRequired(PaymentAuthorityError):
    """Compatibility bridge is required before canonical settlement can post."""


_PAYMENT_TRANSITIONS = {
    CanonicalPaymentStatus.PENDING: {
        CanonicalPaymentStatus.AUTHORIZED,
        CanonicalPaymentStatus.SETTLING,
        CanonicalPaymentStatus.FAILED,
        CanonicalPaymentStatus.VOID,
    },
    CanonicalPaymentStatus.AUTHORIZED: {
        CanonicalPaymentStatus.SETTLING,
        CanonicalPaymentStatus.FAILED,
        CanonicalPaymentStatus.VOID,
    },
    CanonicalPaymentStatus.SETTLING: {
        CanonicalPaymentStatus.FAILED,
    },
    CanonicalPaymentStatus.SETTLED: set(),
    CanonicalPaymentStatus.FAILED: set(),
    CanonicalPaymentStatus.VOID: set(),
    CanonicalPaymentStatus.PARTIALLY_REFUNDED: set(),
    CanonicalPaymentStatus.REFUNDED: set(),
}

_ACTIVE_REFUND_STATUSES = {
    CanonicalRefundStatus.REQUESTED,
    CanonicalRefundStatus.PENDING,
    CanonicalRefundStatus.SETTLED,
}


def _normalized_currency(value: str) -> str:
    return (value or "USD").strip().upper()


def _normalize_allocations(payment: Payment, allocations_payload: list[dict]) -> list[dict]:
    """Return validated allocation facts whose total exactly equals the Payment."""
    if not isinstance(allocations_payload, list) or not allocations_payload:
        raise PaymentAuthorityError("Canonical settlement requires explicit allocations.")

    normalized: list[dict] = []
    obligation_ids: set[int] = set()
    total_cents = 0

    for item in allocations_payload:
        if not isinstance(item, dict):
            raise PaymentAuthorityError("Canonical settlement allocations must be objects.")
        if "obligation_id" not in item or "amount_cents" not in item:
            raise PaymentAuthorityError(
                "Canonical settlement allocation requires obligation_id and amount_cents."
            )
        try:
            obligation_id = int(item["obligation_id"])
            amount_cents = int(item["amount_cents"])
        except (TypeError, ValueError) as exc:
            raise PaymentAuthorityError(
                "Canonical settlement allocation identifiers and amounts must be integers."
            ) from exc
        if obligation_id <= 0:
            raise PaymentAuthorityError("Canonical settlement obligation_id must be positive.")
        if amount_cents <= 0:
            raise PaymentAuthorityError("Canonical settlement allocation amount must be positive.")
        if obligation_id in obligation_ids:
            raise PaymentAuthorityError(
                "Canonical settlement cannot contain duplicate obligation allocations."
            )
        obligation_ids.add(obligation_id)
        total_cents += amount_cents
        normalized.append(
            {"obligation_id": obligation_id, "amount_cents": amount_cents}
        )

    if total_cents != int(payment.amount_cents):
        raise PaymentAuthorityError(
            f"Canonical settlement allocations must equal Payment amount; "
            f"allocated={total_cents}, payment={payment.amount_cents}."
        )
    return normalized


def _assert_provider_facts(
    *,
    provider_owner: str,
    provider: str,
    stored_intent_id: str = "",
    incoming_intent_id: str = "",
    stored_payment_id: str = "",
    incoming_payment_id: str = "",
    stored_refund_id: str = "",
    incoming_refund_id: str = "",
) -> None:
    if provider and provider_owner not in ("", provider):
        raise IdempotencyConflict("Provider ownership conflicts with canonical facts.")
    if incoming_intent_id and stored_intent_id not in ("", incoming_intent_id):
        raise IdempotencyConflict("provider_intent_id conflicts with canonical facts.")
    if incoming_payment_id and stored_payment_id not in ("", incoming_payment_id):
        raise IdempotencyConflict("provider_payment_id conflicts with canonical facts.")
    if incoming_refund_id and stored_refund_id not in ("", incoming_refund_id):
        raise IdempotencyConflict("provider_refund_id conflicts with canonical facts.")


def _assert_same_payment_facts(
    payment: Payment,
    *,
    amount_cents: int,
    currency: str,
    household_id,
    finance_payment_id,
    provider: str,
    provider_intent_id: str,
    provider_payment_id: str,
) -> None:
    expected = {
        "amount_cents": int(amount_cents),
        "currency": _normalized_currency(currency),
        "household_id": household_id,
        "finance_payment_id": finance_payment_id,
    }
    for field_name, value in expected.items():
        if getattr(payment, field_name) != value:
            raise IdempotencyConflict(
                f"Canonical Payment idempotency key conflicts on {field_name}."
            )

    _assert_provider_facts(
        provider_owner=payment.provider,
        provider=provider,
        stored_intent_id=payment.provider_intent_id,
        incoming_intent_id=provider_intent_id,
        stored_payment_id=payment.provider_payment_id,
        incoming_payment_id=provider_payment_id,
    )


@transaction.atomic
def create_payment(
    *,
    school_id,
    amount_cents: int,
    idempotency_key: str,
    currency: str = "USD",
    household_id=None,
    finance_payment_id: int | None = None,
    provider: str = "",
    provider_intent_id: str = "",
    provider_payment_id: str = "",
    metadata: dict | None = None,
    created_by=None,
) -> Payment:
    """Create one immutable canonical money-received fact, idempotently."""
    amount_cents = int(amount_cents)
    idempotency_key = (idempotency_key or "").strip()
    currency = _normalized_currency(currency)
    provider = (provider or "").strip()
    provider_intent_id = (provider_intent_id or "").strip()
    provider_payment_id = (provider_payment_id or "").strip()

    if amount_cents <= 0:
        raise PaymentAuthorityError("Canonical Payment amount must be positive.")
    if not idempotency_key:
        raise PaymentAuthorityError("Canonical Payment idempotency_key is required.")
    if (provider_intent_id or provider_payment_id) and not provider:
        raise PaymentAuthorityError("Provider is required when provider identifiers are supplied.")

    existing = Payment.objects.select_for_update().filter(
        school_id=school_id,
        idempotency_key=idempotency_key,
    ).first()
    if existing is not None:
        _assert_same_payment_facts(
            existing,
            amount_cents=amount_cents,
            currency=currency,
            household_id=household_id,
            finance_payment_id=finance_payment_id,
            provider=provider,
            provider_intent_id=provider_intent_id,
            provider_payment_id=provider_payment_id,
        )
        return existing

    payment = Payment(
        school_id=school_id,
        household_id=household_id,
        finance_payment_id=finance_payment_id,
        amount_cents=amount_cents,
        currency=currency,
        status=CanonicalPaymentStatus.PENDING,
        provider=provider,
        provider_intent_id=provider_intent_id,
        provider_payment_id=provider_payment_id,
        idempotency_key=idempotency_key,
        metadata=metadata or {},
        created_by=created_by,
    )
    payment.full_clean()
    payment.save()
    return payment


@transaction.atomic
def bind_payment_provider(
    *,
    payment: Payment,
    provider: str,
    provider_intent_id: str = "",
    provider_payment_id: str = "",
) -> Payment:
    """Bind provider identifiers once; they cannot later be reassigned."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    provider = (provider or "").strip()
    provider_intent_id = (provider_intent_id or "").strip()
    provider_payment_id = (provider_payment_id or "").strip()
    if not provider:
        raise PaymentAuthorityError("Provider is required when binding provider identifiers.")

    _assert_provider_facts(
        provider_owner=payment.provider,
        provider=provider,
        stored_intent_id=payment.provider_intent_id,
        incoming_intent_id=provider_intent_id,
        stored_payment_id=payment.provider_payment_id,
        incoming_payment_id=provider_payment_id,
    )

    payment.provider = provider
    if provider_intent_id:
        payment.provider_intent_id = provider_intent_id
    if provider_payment_id:
        payment.provider_payment_id = provider_payment_id
    payment.full_clean()
    payment.save(
        update_fields=[
            "provider",
            "provider_intent_id",
            "provider_payment_id",
            "updated_at",
        ]
    )
    return payment


@transaction.atomic
def transition_payment_status(*, payment: Payment, target_status: str) -> Payment:
    """Apply non-financial lifecycle transitions; settlement/refunds use dedicated services."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    target_status = str(target_status)
    if target_status == payment.status:
        return payment
    if target_status in {
        CanonicalPaymentStatus.SETTLED,
        CanonicalPaymentStatus.PARTIALLY_REFUNDED,
        CanonicalPaymentStatus.REFUNDED,
    }:
        raise InvalidPaymentState(
            "Settlement and refund states require their dedicated financial service."
        )
    if target_status not in _PAYMENT_TRANSITIONS.get(payment.status, set()):
        raise InvalidPaymentState(
            f"Canonical Payment cannot transition from {payment.status} to {target_status}."
        )

    payment.status = target_status
    update_fields = ["status", "updated_at"]
    if target_status == CanonicalPaymentStatus.AUTHORIZED:
        payment.authorized_at = timezone.now()
        update_fields.append("authorized_at")
    if target_status == CanonicalPaymentStatus.VOID:
        payment.voided_at = timezone.now()
        update_fields.append("voided_at")
    payment.save(update_fields=update_fields)
    return payment


def _legacy_payment_for(payment: Payment) -> FinancePayment:
    if not payment.finance_payment_id:
        raise PaymentCompatibilityRequired(
            "Canonical Payment has no FinancePayment compatibility link."
        )
    legacy_payment = FinancePayment.objects.select_for_update().filter(
        pk=payment.finance_payment_id,
        school_id=payment.school_id,
    ).first()
    if legacy_payment is None:
        raise PaymentCompatibilityRequired(
            "Canonical Payment FinancePayment compatibility record was not found."
        )
    if int(legacy_payment.amount_cents) != int(payment.amount_cents):
        raise PaymentCompatibilityRequired(
            "Canonical Payment amount does not match FinancePayment compatibility record."
        )
    if _normalized_currency(legacy_payment.currency) != payment.currency:
        raise PaymentCompatibilityRequired(
            "Canonical Payment currency does not match FinancePayment compatibility record."
        )
    return legacy_payment


def _assert_settlement_replay(
    *,
    payment: Payment,
    allocations_payload: list[dict],
    provider: str,
    provider_intent_id: str,
    provider_payment_id: str,
) -> None:
    normalized = _normalize_allocations(payment, allocations_payload)
    _assert_provider_facts(
        provider_owner=payment.provider,
        provider=provider,
        stored_intent_id=payment.provider_intent_id,
        incoming_intent_id=provider_intent_id,
        stored_payment_id=payment.provider_payment_id,
        incoming_payment_id=provider_payment_id,
    )

    legacy_payment = _legacy_payment_for(payment)
    existing_allocations = sorted(
        (int(allocation.obligation_id), int(allocation.amount_cents))
        for allocation in legacy_payment.allocations.all()
    )
    requested_allocations = sorted(
        (item["obligation_id"], item["amount_cents"]) for item in normalized
    )
    if existing_allocations != requested_allocations:
        raise IdempotencyConflict(
            "Canonical settlement replay conflicts with existing allocation facts."
        )


@transaction.atomic
def settle_payment(
    *,
    payment: Payment,
    allocations_payload: list[dict],
    provider: str = "",
    provider_intent_id: str = "",
    provider_payment_id: str = "",
) -> Payment:
    """
    Settle canonical money movement and only then invoke the legacy allocation bridge.

    No Accounting/Student Accounts effect occurs in PENDING/AUTHORIZED/SETTLING.
    """
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    provider = (provider or "").strip()
    provider_intent_id = (provider_intent_id or "").strip()
    provider_payment_id = (provider_payment_id or "").strip()

    if payment.status == CanonicalPaymentStatus.SETTLED:
        _assert_settlement_replay(
            payment=payment,
            allocations_payload=allocations_payload,
            provider=provider,
            provider_intent_id=provider_intent_id,
            provider_payment_id=provider_payment_id,
        )
        return payment
    if payment.status in {
        CanonicalPaymentStatus.FAILED,
        CanonicalPaymentStatus.VOID,
        CanonicalPaymentStatus.PARTIALLY_REFUNDED,
        CanonicalPaymentStatus.REFUNDED,
    }:
        raise InvalidPaymentState(
            f"Canonical Payment in {payment.status} cannot settle."
        )

    normalized_allocations = _normalize_allocations(payment, allocations_payload)
    legacy_payment = _legacy_payment_for(payment)

    effective_provider = provider or payment.provider
    if (provider_intent_id or provider_payment_id) and not effective_provider:
        raise PaymentAuthorityError("Provider is required when provider identifiers are supplied.")
    if effective_provider and (provider or provider_intent_id or provider_payment_id):
        payment = bind_payment_provider(
            payment=payment,
            provider=effective_provider,
            provider_intent_id=provider_intent_id,
            provider_payment_id=provider_payment_id,
        )

    settle_payment_and_allocate(
        payment=legacy_payment,
        allocations_payload=normalized_allocations,
    )
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    payment.status = CanonicalPaymentStatus.SETTLED
    payment.settled_at = timezone.now()
    payment.save(update_fields=["status", "settled_at", "updated_at"])
    return payment


def _assert_same_refund_facts(
    refund: Refund,
    *,
    payment: Payment,
    amount_cents: int,
    provider: str,
) -> None:
    if refund.payment_id != payment.pk:
        raise IdempotencyConflict("Canonical Refund idempotency key belongs to another Payment.")
    if int(refund.amount_cents) != int(amount_cents):
        raise IdempotencyConflict("Canonical Refund idempotency key conflicts on amount_cents.")
    _assert_provider_facts(
        provider_owner=refund.provider,
        provider=provider,
    )


@transaction.atomic
def request_refund(
    *,
    payment: Payment,
    amount_cents: int,
    idempotency_key: str,
    provider: str = "",
    metadata: dict | None = None,
    created_by=None,
) -> Refund:
    """
    Reserve refund capacity without posting any Accounting/Student Accounts effect.

    REQUESTED, PENDING, and SETTLED refunds all reserve capacity so concurrent
    requests cannot over-refund the original Payment.
    """
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    amount_cents = int(amount_cents)
    idempotency_key = (idempotency_key or "").strip()
    provider = (provider or payment.provider or "").strip()

    if amount_cents <= 0:
        raise PaymentAuthorityError("Canonical Refund amount must be positive.")
    if not idempotency_key:
        raise PaymentAuthorityError("Canonical Refund idempotency_key is required.")
    if payment.provider and provider and provider != payment.provider:
        raise PaymentAuthorityError("Canonical Refund provider must match Payment provider.")

    existing = Refund.objects.select_for_update().filter(
        school_id=payment.school_id,
        idempotency_key=idempotency_key,
    ).first()
    if existing is not None:
        _assert_same_refund_facts(
            existing,
            payment=payment,
            amount_cents=amount_cents,
            provider=provider,
        )
        return existing

    if payment.status not in {
        CanonicalPaymentStatus.SETTLED,
        CanonicalPaymentStatus.PARTIALLY_REFUNDED,
    }:
        raise InvalidPaymentState(
            f"Canonical Payment in {payment.status} cannot be refunded."
        )

    reserved_cents = (
        payment.refunds.filter(status__in=_ACTIVE_REFUND_STATUSES)
        .aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    if int(reserved_cents) + amount_cents > int(payment.amount_cents):
        raise CanonicalOverRefundError(
            f"Refund would exceed canonical Payment {payment.pk}; "
            f"reserved={reserved_cents}, requested={amount_cents}, "
            f"payment={payment.amount_cents}."
        )

    refund = Refund(
        school_id=payment.school_id,
        payment=payment,
        amount_cents=amount_cents,
        currency=payment.currency,
        status=CanonicalRefundStatus.REQUESTED,
        provider=provider,
        idempotency_key=idempotency_key,
        metadata=metadata or {},
        created_by=created_by,
    )
    refund.full_clean()
    refund.save()
    return refund


@transaction.atomic
def mark_refund_pending(
    *,
    refund: Refund,
    provider: str,
    provider_refund_id: str = "",
) -> Refund:
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    provider = (provider or "").strip()
    provider_refund_id = (provider_refund_id or "").strip()

    if refund.status == CanonicalRefundStatus.PENDING:
        _assert_provider_facts(
            provider_owner=refund.provider,
            provider=provider,
            stored_refund_id=refund.provider_refund_id,
            incoming_refund_id=provider_refund_id,
        )
        return refund
    if refund.status != CanonicalRefundStatus.REQUESTED:
        raise InvalidPaymentState(
            f"Canonical Refund in {refund.status} cannot become pending."
        )
    if not provider:
        raise PaymentAuthorityError("Provider is required for a pending provider refund.")

    _assert_provider_facts(
        provider_owner=refund.provider,
        provider=provider,
        stored_refund_id=refund.provider_refund_id,
        incoming_refund_id=provider_refund_id,
    )

    refund.provider = provider
    if provider_refund_id:
        refund.provider_refund_id = provider_refund_id
    refund.status = CanonicalRefundStatus.PENDING
    refund.full_clean()
    refund.save(
        update_fields=[
            "provider",
            "provider_refund_id",
            "status",
            "updated_at",
        ]
    )
    return refund


@transaction.atomic
def settle_refund(
    *,
    refund: Refund,
    provider: str = "",
    provider_refund_id: str = "",
) -> Refund:
    """
    Confirm provider settlement, then and only then post the compatibility refund.
    """
    refund = Refund.objects.select_for_update().select_related("payment").get(pk=refund.pk)
    payment = Payment.objects.select_for_update().get(pk=refund.payment_id)
    provider = (provider or refund.provider or payment.provider or "").strip()
    provider_refund_id = (provider_refund_id or refund.provider_refund_id or "").strip()

    if refund.status == CanonicalRefundStatus.SETTLED:
        _assert_provider_facts(
            provider_owner=refund.provider,
            provider=provider,
            stored_refund_id=refund.provider_refund_id,
            incoming_refund_id=provider_refund_id,
        )
        return refund
    if refund.status not in {
        CanonicalRefundStatus.REQUESTED,
        CanonicalRefundStatus.PENDING,
    }:
        raise InvalidPaymentState(
            f"Canonical Refund in {refund.status} cannot settle."
        )

    _assert_provider_facts(
        provider_owner=refund.provider,
        provider=provider,
        stored_refund_id=refund.provider_refund_id,
        incoming_refund_id=provider_refund_id,
    )

    legacy_payment = _legacy_payment_for(payment)
    legacy_idempotency_key = f"canonical_refund:{refund.pk}"
    legacy_refund = legacy_payment.refunds.filter(
        idempotency_key=legacy_idempotency_key,
    ).first()
    if legacy_refund is None:
        legacy_refund = initiate_refund(
            payment=legacy_payment,
            amount_cents=refund.amount_cents,
            processor=legacy_payment.processor,
            created_by=refund.created_by,
            idempotency_key=legacy_idempotency_key,
        )

    legacy_refund.status = LegacyPaymentStatus.SETTLED
    if provider_refund_id:
        legacy_refund.processor_refund_id = provider_refund_id
    legacy_refund.save(update_fields=["status", "processor_refund_id", "updated_at"])

    refund.provider = provider
    refund.provider_refund_id = provider_refund_id
    refund.finance_refund_id = legacy_refund.pk
    refund.status = CanonicalRefundStatus.SETTLED
    refund.settled_at = timezone.now()
    refund.save(
        update_fields=[
            "provider",
            "provider_refund_id",
            "finance_refund_id",
            "status",
            "settled_at",
            "updated_at",
        ]
    )

    settled_total = (
        payment.refunds.filter(status=CanonicalRefundStatus.SETTLED)
        .aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    payment.status = (
        CanonicalPaymentStatus.REFUNDED
        if int(settled_total) == int(payment.amount_cents)
        else CanonicalPaymentStatus.PARTIALLY_REFUNDED
    )
    payment.save(update_fields=["status", "updated_at"])
    return refund


@transaction.atomic
def fail_refund(*, refund: Refund) -> Refund:
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    if refund.status == CanonicalRefundStatus.FAILED:
        return refund
    if refund.status not in {
        CanonicalRefundStatus.REQUESTED,
        CanonicalRefundStatus.PENDING,
    }:
        raise InvalidPaymentState(
            f"Canonical Refund in {refund.status} cannot fail."
        )
    refund.status = CanonicalRefundStatus.FAILED
    refund.save(update_fields=["status", "updated_at"])
    return refund


@transaction.atomic
def cancel_refund(*, refund: Refund) -> Refund:
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    if refund.status == CanonicalRefundStatus.CANCELED:
        return refund
    if refund.status not in {
        CanonicalRefundStatus.REQUESTED,
        CanonicalRefundStatus.PENDING,
    }:
        raise InvalidPaymentState(
            f"Canonical Refund in {refund.status} cannot be canceled."
        )
    refund.status = CanonicalRefundStatus.CANCELED
    refund.save(update_fields=["status", "updated_at"])
    return refund
