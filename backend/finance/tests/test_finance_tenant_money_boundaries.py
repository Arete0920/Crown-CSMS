from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from core.models import School, UserAccount
from finance.models import (
    FinanceAllocation,
    FinanceInvoice,
    FinanceInvoiceLine,
    FinanceObligation,
    FinancePayment,
    FinanceRefund,
    MoneyStatus,
    ObligationType,
    PaymentStatus,
    Processor,
)


pytestmark = pytest.mark.django_db


def _user(name, school):
    return UserAccount.objects.create_user(
        username=name,
        password="pass",
        email=f"{name}@example.com",
        school_id=school.id,
    )


def _obligation(school, payer, amount=10_000):
    return FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Tenant boundary tuition",
        due_date=date.today() + timedelta(days=30),
        amount_cents=amount,
        currency="USD",
    )


def test_invoice_line_rejects_cross_school_obligation():
    school_a = School.objects.create(name="Invoice school A")
    school_b = School.objects.create(name="Invoice school B")
    payer_a = _user("invoice_a", school_a)
    payer_b = _user("invoice_b", school_b)
    obligation_b = _obligation(school_b, payer_b)
    invoice_a = FinanceInvoice.objects.create(
        school=school_a,
        payer_user=payer_a,
        period_start=date.today(),
        period_end=date.today() + timedelta(days=30),
        due_date=date.today() + timedelta(days=30),
    )

    with pytest.raises(ValidationError, match="same school"):
        FinanceInvoiceLine.objects.create(
            invoice=invoice_a,
            obligation=obligation_b,
            amount_cents=obligation_b.amount_cents,
        )


def test_invoice_line_rejects_cross_payer_obligation():
    school = School.objects.create(name="Invoice payer school")
    payer_a = _user("invoice_payer_a", school)
    payer_b = _user("invoice_payer_b", school)
    obligation_b = _obligation(school, payer_b)
    invoice_a = FinanceInvoice.objects.create(
        school=school,
        payer_user=payer_a,
        period_start=date.today(),
        period_end=date.today() + timedelta(days=30),
        due_date=date.today() + timedelta(days=30),
    )

    with pytest.raises(ValidationError, match="same payer"):
        FinanceInvoiceLine.objects.create(
            invoice=invoice_a,
            obligation=obligation_b,
            amount_cents=obligation_b.amount_cents,
        )


def test_allocation_rejects_cross_school_and_cross_payer():
    school_a = School.objects.create(name="Allocation school A")
    school_b = School.objects.create(name="Allocation school B")
    payer_a = _user("allocation_a", school_a)
    payer_b = _user("allocation_b", school_b)
    obligation_b = _obligation(school_b, payer_b)
    payment_a = FinancePayment.objects.create(
        school=school_a,
        payer_user=payer_a,
        amount_cents=10_000,
        currency="USD",
        status=PaymentStatus.PENDING,
        processor=Processor.MANUAL,
    )

    with pytest.raises(ValidationError, match="same school"):
        FinanceAllocation.objects.create(
            school=school_a,
            payment=payment_a,
            obligation=obligation_b,
            amount_cents=10_000,
        )


def test_refund_rejects_cross_school_payment():
    school_a = School.objects.create(name="Refund school A")
    school_b = School.objects.create(name="Refund school B")
    payer_a = _user("refund_a", school_a)
    payment_a = FinancePayment.objects.create(
        school=school_a,
        payer_user=payer_a,
        amount_cents=10_000,
        currency="USD",
        status=PaymentStatus.SETTLED,
        processor=Processor.MANUAL,
    )

    with pytest.raises(ValidationError, match="same school"):
        FinanceRefund.objects.create(
            school=school_b,
            payment=payment_a,
            amount_cents=1_000,
            currency="USD",
            processor=Processor.MANUAL,
        )


def test_refund_rejects_currency_drift():
    school = School.objects.create(name="Refund currency school")
    payer = _user("refund_currency", school)
    payment = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=10_000,
        currency="USD",
        status=PaymentStatus.SETTLED,
        processor=Processor.MANUAL,
    )

    with pytest.raises(ValidationError, match="currency"):
        FinanceRefund.objects.create(
            school=school,
            payment=payment,
            amount_cents=1_000,
            currency="EUR",
            processor=Processor.MANUAL,
        )
