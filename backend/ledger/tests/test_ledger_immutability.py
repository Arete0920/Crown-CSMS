"""
Phase 2 Priority 6 — Ledger immutability proof tests.

Guards locked in CI:
  1. Charge.amount cannot be changed after creation (ValidationError)
  2. Payment.amount cannot be changed after creation (ValidationError)
  3. Charge.account_id cannot be moved to a different account after creation (ValidationError)
  4. Charge.is_void CAN be flipped True (not a money-critical field — reversal path is valid)
  5. Charge.description IS mutable (billing corrections are an allowed workflow)
  6. Payment.source is immutable after creation (ValidationError)
  7. Payment.reference is immutable after creation (ValidationError)

No new models, no migrations, no seed required.
"""
import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment

pytestmark = pytest.mark.django_db


def _school_and_account():
    sid = uuid.uuid4()
    School.objects.get_or_create(id=sid, defaults={"name": f"Immut-School-{sid}"})
    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
    acct = LedgerAccount.objects.create(school_id=sid, household=hh)
    return sid, acct


def _make_charge(sid, acct, amount="250.00", description="Tuition"):
    return Charge.objects.create(
        school_id=sid,
        account=acct,
        description=description,
        amount=Decimal(amount),
    )


def _make_payment(sid, acct, amount="250.00"):
    return Payment.objects.create(
        school_id=sid,
        account=acct,
        source="EXTERNAL",
        reference="ref-abc",
        amount=Decimal(amount),
    )


# ---------------------------------------------------------------------------
# 1. Charge.amount is immutable after creation
# ---------------------------------------------------------------------------

def test_charge_amount_is_immutable():
    sid, acct = _school_and_account()
    charge = _make_charge(sid, acct, amount="500.00")

    charge.amount = Decimal("999.00")
    with pytest.raises(ValidationError) as exc_info:
        charge.save()

    errors = exc_info.value.message_dict
    assert "amount" in errors, f"Expected 'amount' in error keys, got: {errors}"
    # DB should still show the original value
    charge.refresh_from_db()
    assert charge.amount == Decimal("500.00")


# ---------------------------------------------------------------------------
# 2. Payment.amount is immutable after creation
# ---------------------------------------------------------------------------

def test_payment_amount_is_immutable():
    sid, acct = _school_and_account()
    payment = _make_payment(sid, acct, amount="300.00")

    payment.amount = Decimal("1.00")
    with pytest.raises(ValidationError) as exc_info:
        payment.save()

    errors = exc_info.value.message_dict
    assert "amount" in errors, f"Expected 'amount' in error keys, got: {errors}"
    payment.refresh_from_db()
    assert payment.amount == Decimal("300.00")


# ---------------------------------------------------------------------------
# 3. Charge.account_id is immutable after creation
# ---------------------------------------------------------------------------

def test_charge_account_is_immutable():
    sid, acct = _school_and_account()
    charge = _make_charge(sid, acct)

    # Create a second account to try to reassign to
    hh2 = Household.objects.create(school_id=sid, name=f"HH2-{uuid.uuid4()}")
    acct2 = LedgerAccount.objects.create(school_id=sid, household=hh2)

    charge.account = acct2
    with pytest.raises(ValidationError) as exc_info:
        charge.save()

    errors = exc_info.value.message_dict
    assert "account_id" in errors or "account" in errors, f"Expected account key in errors, got: {errors}"


# ---------------------------------------------------------------------------
# 4. Charge.is_void CAN be flipped (not money-critical — reversal path)
# ---------------------------------------------------------------------------

def test_charge_is_void_is_mutable():
    sid, acct = _school_and_account()
    charge = _make_charge(sid, acct)
    assert charge.is_void is False

    # This must NOT raise — voiding is the legitimate correction path
    charge.is_void = True
    charge.save()  # should succeed

    charge.refresh_from_db()
    assert charge.is_void is True


# ---------------------------------------------------------------------------
# 5. Charge.description is mutable (e.g., billing corrections are valid)
# ---------------------------------------------------------------------------

def test_charge_description_is_mutable():
    sid, acct = _school_and_account()
    charge = _make_charge(sid, acct, description="Original Tuition")

    charge.description = "Corrected Tuition"
    charge.save()  # must NOT raise — description changes are allowed

    charge.refresh_from_db()
    assert charge.description == "Corrected Tuition"

# ---------------------------------------------------------------------------
# 6. Payment.source is immutable after creation
# ---------------------------------------------------------------------------

def test_payment_source_is_immutable():
    sid, acct = _school_and_account()
    payment = _make_payment(sid, acct)

    payment.source = "TAMPERED"
    with pytest.raises(ValidationError) as exc_info:
        payment.save()

    errors = exc_info.value.message_dict
    assert "source" in errors, f"Expected 'source' in error keys, got: {errors}"
    payment.refresh_from_db()
    assert payment.source == "EXTERNAL"


# ---------------------------------------------------------------------------
# 7. Payment.reference is immutable after creation
# ---------------------------------------------------------------------------

def test_payment_reference_is_immutable():
    sid, acct = _school_and_account()
    payment = _make_payment(sid, acct)

    payment.reference = "tampered-ref-999"
    with pytest.raises(ValidationError) as exc_info:
        payment.save()

    errors = exc_info.value.message_dict
    assert "reference" in errors, f"Expected 'reference' in error keys, got: {errors}"
    payment.refresh_from_db()
    assert payment.reference == "ref-abc"
