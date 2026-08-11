from decimal import Decimal
from unittest.mock import patch

import pytest

from core.models import School, UserAccount
from finance.models import FinancePayment, PaymentStatus, Processor
from payments.models import GatewayEvent, GatewayEventStatus, GatewayProvider, PaymentIntentRecord, PaymentSupportException
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


def _intent(school, *, metadata=None, provider_payment_id="pay_123", client_reference_id="client_123"):
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
        payload={"intent_id": "intent_123", "payment_id": payment_id, "status": status},
    )


def test_settlement_without_explicit_allocations_fails_and_records_exception():
    school, user = _school_user()
    payment = FinancePayment.objects.create(
        school=school,
        payer_user=user,
        amount_cents=10_000,
        processor=Processor.COMPUWERX,
        processor_payment_id="pay_123",
        status=PaymentStatus.PENDING,
    )
    _intent(school, metadata={"finance_payment_id": payment.id})
    event = _event(school)

    with pytest.raises(SettlementAllocationRequired):
        process_gateway_event_safely(event)

    payment.refresh_from_db()
    event.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
    assert event.status == GatewayEventStatus.FAILED
    assert PaymentSupportException.objects.filter(
        school_id=school.id,
        gateway_event_id=event.id,
        category="gateway_event_processing",
    ).exists()


def test_provider_intent_or_client_reference_is_not_overloaded_as_payment_id():
    school, user = _school_user()
    FinancePayment.objects.create(
        school=school,
        payer_user=user,
        amount_cents=10_000,
        processor=Processor.COMPUWERX,
        processor_payment_id="client_123",
        status=PaymentStatus.PENDING,
    )
    _intent(school, provider_payment_id="pay_real", client_reference_id="client_123")
    event = _event(school, payment_id="pay_real")

    with pytest.raises(UnmatchedPaymentError):
        process_gateway_event_safely(event)

    event.refresh_from_db()
    assert event.status == GatewayEventStatus.FAILED


def test_refund_uses_event_provider_not_hard_coded_processor():
    school, user = _school_user()
    payment = FinancePayment.objects.create(
        school=school,
        payer_user=user,
        amount_cents=10_000,
        processor=Processor.COMPUWERX,
        processor_payment_id="pay_123",
        status=PaymentStatus.SETTLED,
    )
    intent = _intent(school, metadata={"finance_payment_id": payment.id})

    with patch("payments.services.initiate_refund") as initiate:
        _apply_refund(
            intent,
            {"refund_amount": "10.00"},
            provider=GatewayProvider.COMPUWERX,
        )

    assert initiate.call_count == 1
    assert initiate.call_args.kwargs["processor"] == GatewayProvider.COMPUWERX
