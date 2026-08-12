from decimal import Decimal
from unittest.mock import patch

import pytest

from core.models import School, UserAccount
from finance.models import FinancePayment, PaymentStatus, Processor
from payments.models import (
    CanonicalPaymentStatus,
    GatewayEvent,
    GatewayEventStatus,
    GatewayProvider,
    Payment,
    PaymentIntentRecord,
    PaymentSupportException,
)
from payments.services import (
    SettlementAllocationRequired,
    UnmatchedPaymentError,
    _apply_refund,
    process_gateway_event_safely,
)

pytestmark = pytest.mark.django_db


def _school_user():
    school = School.objects.create(name="Payments Option A")
    user = UserAccount.objects.create_user(
        username="payer",
        email="payer@example.com",
        password="pass",
        school=school,
    )
    return school, user


def _payment(school, user, *, provider_id="pay_123", status=PaymentStatus.PENDING):
    return FinancePayment.objects.create(
        school=school,
        payer_user=user,
        amount_cents=10_000,
        processor=Processor.COMPUWERX,
        processor_payment_id=provider_id,
        status=status,
    )


def _intent(
    school,
    *,
    metadata=None,
    provider_payment_id="pay_123",
    client_reference_id="client_123",
):
    return PaymentIntentRecord.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        amount=Decimal("100.00"),
        currency="USD",
        client_reference_id=client_reference_id,
        provider_intent_id="intent_123",
        provider_payment_id=provider_payment_id,
        metadata=metadata or {},
    )


def _event(school, *, status="settled", payment_id="pay_123"):
    return GatewayEvent.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        event_id=f"evt_{status}_{payment_id}",
        event_type="payment.updated",
        provider_intent_id="intent_123",
        provider_payment_id=payment_id,
        raw_body="{}",
        payload={
            "intent_id": "intent_123",
            "payment_id": payment_id,
            "status": status,
        },
    )


def test_settlement_without_explicit_allocations_fails_and_records_exception():
    school, user = _school_user()
    payment = _payment(school, user)
    _intent(school, metadata={"finance_payment_id": payment.id})
    event = _event(school)

    with pytest.raises(SettlementAllocationRequired):
        process_gateway_event_safely(event)

    payment.refresh_from_db()
    event.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
    assert event.status == GatewayEventStatus.FAILED
    assert not Payment.objects.filter(finance_payment_id=payment.id).exists()
    assert PaymentSupportException.objects.filter(
        school_id=school.id,
        gateway_event_id=event.id,
        category="gateway_event_processing",
    ).exists()


def test_provider_intent_or_client_reference_is_not_overloaded_as_payment_id():
    school, user = _school_user()
    _payment(school, user, provider_id="client_123")
    _intent(
        school,
        provider_payment_id="pay_real",
        client_reference_id="client_123",
    )
    event = _event(school, payment_id="pay_real")

    with pytest.raises(UnmatchedPaymentError):
        process_gateway_event_safely(event)
    event.refresh_from_db()
    assert event.status == GatewayEventStatus.FAILED


def test_settlement_event_creates_canonical_payment_and_routes_to_authority():
    school, user = _school_user()
    legacy_payment = _payment(school, user)
    _intent(
        school,
        metadata={
            "finance_payment_id": legacy_payment.id,
            "allocations": [{"obligation_id": 41, "amount_cents": 6_000}],
        },
    )
    event = _event(school)

    with patch("payments.services.settle_payment") as settle:
        process_gateway_event_safely(event)

    canonical = Payment.objects.get(finance_payment_id=legacy_payment.id)
    assert canonical.amount_cents == legacy_payment.amount_cents
    assert canonical.provider == GatewayProvider.COMPUWERX
    assert canonical.provider_intent_id == "intent_123"
    assert canonical.provider_payment_id == "pay_123"
    assert canonical.idempotency_key.startswith("gateway_intent:")
    assert settle.call_count == 1
    assert settle.call_args.kwargs["payment"].pk == canonical.pk
    assert settle.call_args.kwargs["allocations_payload"] == [
        {"obligation_id": 41, "amount_cents": 6_000}
    ]
    event.refresh_from_db()
    assert event.status == GatewayEventStatus.PROCESSED


def test_refund_requires_prior_canonical_settlement_reconciliation():
    school, user = _school_user()
    legacy_payment = _payment(school, user, status=PaymentStatus.SETTLED)
    intent = _intent(school, metadata={"finance_payment_id": legacy_payment.id})
    event = _event(school, status="refunded")

    with pytest.raises(UnmatchedPaymentError, match="settlement reconciliation"):
        _apply_refund(
            event,
            intent,
            {"refund_amount": "10.00"},
            provider=GatewayProvider.COMPUWERX,
        )


def test_refund_routes_through_canonical_authority_and_preserves_provider_refund_id():
    school, user = _school_user()
    legacy_payment = _payment(school, user, status=PaymentStatus.SETTLED)
    intent = _intent(school, metadata={"finance_payment_id": legacy_payment.id})
    event = _event(school, status="refunded")
    Payment.objects.create(
        school_id=school.id,
        finance_payment_id=legacy_payment.id,
        amount_cents=legacy_payment.amount_cents,
        currency="USD",
        status=CanonicalPaymentStatus.SETTLED,
        provider=GatewayProvider.COMPUWERX,
        provider_intent_id="intent_123",
        provider_payment_id="pay_123",
        idempotency_key="canonical-existing",
    )
    refund_sentinel = object()

    with (
        patch("payments.services.request_refund", return_value=refund_sentinel) as request,
        patch("payments.services.settle_refund") as settle,
    ):
        _apply_refund(
            event,
            intent,
            {"refund_amount": "10.00", "refund_id": "refund_real_123"},
            provider=GatewayProvider.COMPUWERX,
        )

    assert request.call_count == 1
    assert request.call_args.kwargs["amount_cents"] == 1_000
    assert request.call_args.kwargs["provider"] == GatewayProvider.COMPUWERX
    assert request.call_args.kwargs["idempotency_key"] == (
        f"gateway_refund_event:{GatewayProvider.COMPUWERX}:{event.event_id}"
    )
    assert settle.call_count == 1
    assert settle.call_args.kwargs["refund"] is refund_sentinel
    assert settle.call_args.kwargs["provider"] == GatewayProvider.COMPUWERX
    assert settle.call_args.kwargs["provider_refund_id"] == "refund_real_123"
