from datetime import date, timedelta
from decimal import Decimal

import pytest

from core.models import School, UserAccount
from finance.models import (
    FinanceAllocation,
    FinanceObligation,
    FinancePayment,
    MoneyStatus,
    ObligationType,
    PaymentStatus as LegacyPaymentStatus,
    Processor,
)
from finance.services import create_invoice_from_obligations
from households.models import Guardian as HouseholdGuardian, Household
from journal.models import JournalEntry
from ledger.models import Allocation as LedgerAllocation
from ledger.models import Charge as LedgerCharge
from ledger.models import LedgerAccount, Payment as LedgerPayment
from payments.authority_services import (
    create_payment,
    request_refund,
    settle_payment,
    settle_refund,
)
from payments.models import CanonicalPaymentStatus, CanonicalRefundStatus


pytestmark = pytest.mark.django_db


def _user(username):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
    )


def _link_household(school, payer):
    household = Household.objects.create(school_id=school.id, name=f"HH-{payer.username}")
    HouseholdGuardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Runtime",
        last_name="Guardian",
        email=payer.email,
        is_primary=True,
    )
    account = LedgerAccount.objects.create(school_id=school.id, household=household)
    return household, account


def test_canonical_payment_and_refund_cross_student_accounts_and_gl_without_mocks():
    school = School.objects.create(name="Option A Runtime Finance")
    payer = _user("option_a_runtime_payer")
    household, ledger_account = _link_household(school, payer)

    obligation = FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Runtime tuition",
        due_date=date.today() + timedelta(days=30),
        amount_cents=10_000,
        currency="USD",
    )
    invoice = create_invoice_from_obligations(
        school=school,
        payer_user=payer,
        period_start=date.today(),
        period_end=date.today() + timedelta(days=30),
        due_date=date.today() + timedelta(days=30),
        obligations=[obligation],
        created_by=payer,
    )
    assert invoice.total_cents == 10_000
    assert invoice.lines.get().obligation_id == obligation.id

    legacy_payment = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=10_000,
        currency="USD",
        status=LegacyPaymentStatus.PENDING,
        processor=Processor.MANUAL,
        created_by=payer,
    )
    canonical_payment = create_payment(
        school_id=school.id,
        household_id=household.id,
        finance_payment_id=legacy_payment.id,
        amount_cents=10_000,
        currency="USD",
        idempotency_key="runtime-payment-1",
        created_by=payer,
    )

    canonical_payment = settle_payment(
        payment=canonical_payment,
        allocations_payload=[{"obligation_id": obligation.id, "amount_cents": 10_000}],
    )
    legacy_payment.refresh_from_db()

    assert canonical_payment.status == CanonicalPaymentStatus.SETTLED
    assert legacy_payment.status == LegacyPaymentStatus.SETTLED
    assert FinanceAllocation.objects.filter(
        payment=legacy_payment,
        obligation=obligation,
        amount_cents=10_000,
    ).exists()

    ledger_charge = LedgerCharge.objects.get(
        school_id=school.id,
        account=ledger_account,
        description=f"finance_obligation:{obligation.id}",
    )
    ledger_payment = LedgerPayment.objects.get(
        school_id=school.id,
        account=ledger_account,
        reference=f"finance_payment:{legacy_payment.id}",
    )
    assert ledger_payment.amount == Decimal("100.00")
    assert LedgerAllocation.objects.filter(
        payment=ledger_payment,
        charge=ledger_charge,
        amount=Decimal("100.00"),
    ).exists()

    charge_entry = JournalEntry.objects.get(
        reference_type="charge",
        reference_id=ledger_charge.id,
    )
    payment_entry = JournalEntry.objects.get(
        reference_type="payment",
        reference_id=ledger_payment.id,
    )
    charge_lines = {line.account.code: line for line in charge_entry.lines.select_related("account")}
    payment_lines = {line.account.code: line for line in payment_entry.lines.select_related("account")}
    assert charge_lines["1100"].debit == Decimal("100.00")
    assert charge_lines["4000"].credit == Decimal("100.00")
    assert payment_lines["1000"].debit == Decimal("100.00")
    assert payment_lines["1100"].credit == Decimal("100.00")

    refund = request_refund(
        payment=canonical_payment,
        amount_cents=2_500,
        idempotency_key="runtime-refund-1",
        created_by=payer,
    )
    assert refund.status == CanonicalRefundStatus.REQUESTED
    assert not LedgerCharge.objects.filter(
        school_id=school.id,
        account=ledger_account,
        description__startswith="finance_refund:",
    ).exists()

    refund = settle_refund(refund=refund)
    canonical_payment.refresh_from_db()
    assert refund.status == CanonicalRefundStatus.SETTLED
    assert canonical_payment.status == CanonicalPaymentStatus.PARTIALLY_REFUNDED

    refund_charge = LedgerCharge.objects.get(
        school_id=school.id,
        account=ledger_account,
        description=f"finance_refund:{refund.finance_refund_id}",
    )
    refund_entry = JournalEntry.objects.get(
        reference_type="finance_refund",
        reference_id=refund_charge.id,
    )
    refund_lines = {line.account.code: line for line in refund_entry.lines.select_related("account")}
    assert set(refund_lines) == {"1000", "1100"}
    assert refund_lines["1100"].debit == Decimal("25.00")
    assert refund_lines["1000"].credit == Decimal("25.00")
    assert not JournalEntry.objects.filter(
        reference_type="charge",
        reference_id=refund_charge.id,
    ).exists()
