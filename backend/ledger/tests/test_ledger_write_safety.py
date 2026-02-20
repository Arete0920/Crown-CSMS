"""
Phase 2 Priority 4 — Ledger write-safety proof tests.

Guards locked in CI:
  1. create_charge rejects amount <= 0 (negative and zero)
  2. create_charge accepts positive amounts (happy path)
  3. record_payment rejects amount <= 0 (pre-existing guard, proofed here)
  4. record_payment + allocate rejects over-allocation (pre-existing, proofed here)

No new models, no migrations, no seed required.
"""
import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment

pytestmark = pytest.mark.django_db

CHARGES_URL = "/api/v1/ledger/charges/"
PAYMENTS_URL = "/api/v1/ledger/payments/"


def _school_and_account():
    sid = uuid.uuid4()
    School.objects.get_or_create(id=sid, defaults={"name": f"WS-{sid}"})
    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
    acct = LedgerAccount.objects.create(school_id=sid, household=hh)
    User = get_user_model()
    user = User.objects.create_user(username=f"u-{uuid.uuid4()}", password="pass!")
    return sid, acct, user


def _auth_client(user, sid):
    c = Client()
    c.force_login(user)
    return c, {"HTTP_X_SCHOOL_ID": str(sid), "content_type": "application/json"}


# ---------------------------------------------------------------------------
# 1. create_charge: negative amount rejected
# ---------------------------------------------------------------------------

def test_create_charge_rejects_negative_amount():
    sid, acct, user = _school_and_account()
    c, kwargs = _auth_client(user, sid)
    resp = c.post(
        CHARGES_URL,
        data={"account_id": str(acct.id), "description": "Bad", "amount": "-50.00"},
        **kwargs,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.content}"
    assert Charge.objects.filter(account=acct).count() == 0


# ---------------------------------------------------------------------------
# 2. create_charge: zero amount rejected
# ---------------------------------------------------------------------------

def test_create_charge_rejects_zero_amount():
    sid, acct, user = _school_and_account()
    c, kwargs = _auth_client(user, sid)
    resp = c.post(
        CHARGES_URL,
        data={"account_id": str(acct.id), "description": "Zero", "amount": "0.00"},
        **kwargs,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.content}"
    assert Charge.objects.filter(account=acct).count() == 0


# ---------------------------------------------------------------------------
# 3. create_charge: positive amount accepted (baseline sanity)
# ---------------------------------------------------------------------------

def test_create_charge_accepts_positive_amount():
    sid, acct, user = _school_and_account()
    c, kwargs = _auth_client(user, sid)
    resp = c.post(
        CHARGES_URL,
        data={"account_id": str(acct.id), "description": "Tuition", "amount": "1000.00"},
        **kwargs,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.content}"
    assert Charge.objects.filter(account=acct, amount=Decimal("1000.00")).count() == 1


# ---------------------------------------------------------------------------
# 4. record_payment: negative amount rejected (pre-existing guard, proofed)
# ---------------------------------------------------------------------------

def test_record_payment_rejects_negative_amount():
    sid, acct, user = _school_and_account()
    c, kwargs = _auth_client(user, sid)
    resp = c.post(
        PAYMENTS_URL,
        data={"account_id": str(acct.id), "amount": "-100.00"},
        **kwargs,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.content}"
    assert Payment.objects.filter(account=acct).count() == 0


# ---------------------------------------------------------------------------
# 5. record_payment + allocate: over-allocation rejected (pre-existing, proofed)
# ---------------------------------------------------------------------------

def test_record_payment_rejects_over_allocation():
    """
    Payment of 50 cannot allocate 100 to a charge — should return 400.
    """
    sid, acct, user = _school_and_account()
    charge = Charge.objects.create(
        school_id=sid, account=acct, description="Fee", amount=Decimal("200.00")
    )
    c, kwargs = _auth_client(user, sid)
    resp = c.post(
        PAYMENTS_URL,
        data={
            "account_id": str(acct.id),
            "amount": "50.00",
            "allocations": [{"charge_id": str(charge.id), "amount": "100.00"}],
        },
        **kwargs,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.content}"
    # No payment row should have persisted due to atomic rollback
    assert Payment.objects.filter(account=acct).count() == 0
