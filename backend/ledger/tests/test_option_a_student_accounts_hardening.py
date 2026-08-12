import uuid
from decimal import Decimal

import pytest

from core.models import School
from households.models import Household
from journal.models import JournalEntry
from ledger.models import Charge, LedgerAccount, Payment
from ledger.services import account_balance, allocate_payment_fifo, build_account_statement


pytestmark = pytest.mark.django_db


def _school_id(label):
    return School.objects.create(name=f"{label}-{uuid.uuid4()}").id


def _account(school_id):
    household = Household.objects.create(school_id=school_id, name=f"HH-{uuid.uuid4()}")
    return LedgerAccount.objects.create(school_id=school_id, household=household)


def test_fifo_rejects_void_payment():
    school_id = _school_id("Option A FIFO")
    account = _account(school_id)
    Charge.objects.create(
        school_id=school_id,
        account=account,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    payment = Payment.objects.create(
        school_id=school_id,
        account=account,
        amount=Decimal("100.00"),
        is_void=True,
    )

    assert not JournalEntry.objects.filter(reference_type="payment", reference_id=payment.id).exists()
    with pytest.raises(ValueError, match="void payment"):
        allocate_payment_fifo(school_id=school_id, payment=payment)


def test_balance_and_statement_ignore_void_payment_allocations():
    school_id = _school_id("Option A void payment")
    account = _account(school_id)
    Charge.objects.create(
        school_id=school_id,
        account=account,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    payment = Payment.objects.create(
        school_id=school_id,
        account=account,
        amount=Decimal("100.00"),
    )

    result = allocate_payment_fifo(school_id=school_id, payment=payment)
    assert result.remaining_unallocated == Decimal("0.00")
    assert account_balance(account) == Decimal("0.00")

    payment.is_void = True
    payment.save(update_fields=["is_void"])

    assert account_balance(account) == Decimal("100.00")
    statement = build_account_statement(school_id=school_id, account=account)
    assert statement["balance"] == "100.00"
    assert [entry["type"] for entry in statement["entries"]] == ["CHARGE"]


def test_void_charge_has_zero_remaining_balance_and_is_excluded_from_statement():
    school_id = _school_id("Option A void charge")
    account = _account(school_id)
    Charge.objects.create(
        school_id=school_id,
        account=account,
        description="Fee",
        amount=Decimal("25.00"),
        is_void=True,
    )

    assert account_balance(account) == Decimal("0.00")
    statement = build_account_statement(school_id=school_id, account=account)
    assert statement["balance"] == "0.00"
    assert statement["entries"] == []


def test_finance_refund_charge_reopens_ar_without_recognizing_revenue():
    school_id = _school_id("Option A refund reversal")
    account = _account(school_id)
    charge = Charge.objects.create(
        school_id=school_id,
        account=account,
        description="finance_refund:123",
        amount=Decimal("25.00"),
    )

    assert not JournalEntry.objects.filter(
        reference_type="charge",
        reference_id=charge.id,
    ).exists()

    entry = JournalEntry.objects.get(
        reference_type="finance_refund",
        reference_id=charge.id,
    )
    lines = {line.account.code: line for line in entry.lines.select_related("account").all()}

    assert set(lines) == {"1000", "1100"}
    assert lines["1100"].debit == Decimal("25.00")
    assert lines["1100"].credit == Decimal("0.00")
    assert lines["1000"].debit == Decimal("0.00")
    assert lines["1000"].credit == Decimal("25.00")
