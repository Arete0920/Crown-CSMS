"""
Phase 2 Priority 5 — Void endpoint API proof tests.

Guards locked in CI:
  1. POST /api/v1/ledger/charges/<id>/void/ marks charge is_void=True → 200
  2. void_charge is idempotent (second call returns 200, no error)
  3. void_charge deletes allocations tied to the charge
  4. POST /api/v1/ledger/payments/<id>/void/ marks payment is_void=True → 200
  5. void_payment is idempotent (second call returns 200, no error)
  6. void_payment deletes allocations tied to the payment

No migrations, no seed required. All state built inline.
"""
import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment, Allocation

pytestmark = pytest.mark.django_db

VOID_CHARGE_URL = "/api/v1/ledger/charges/{}/void/"
VOID_PAYMENT_URL = "/api/v1/ledger/payments/{}/void/"


def _school_and_account():
    sid = uuid.uuid4()
    School.objects.get_or_create(id=sid, defaults={"name": f"VoidTest-{sid}"})
    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
    acct = LedgerAccount.objects.create(school_id=sid, household=hh)
    User = get_user_model()
    user = User.objects.create_user(username=f"u-{uuid.uuid4()}", password="pass!")
    return sid, acct, user


def _auth_client(user, sid):
    c = Client()
    c.force_login(user)
    return c, {"HTTP_X_SCHOOL_ID": str(sid)}


def _make_charge(sid, acct, amount="100.00"):
    return Charge.objects.create(
        school_id=sid,
        account=acct,
        description="Void test charge",
        amount=Decimal(amount),
    )


def _make_payment(sid, acct, amount="100.00"):
    return Payment.objects.create(
        school_id=sid,
        account=acct,
        source="EXTERNAL",
        reference=f"ref-{uuid.uuid4()}",
        amount=Decimal(amount),
    )


# ---------------------------------------------------------------------------
# 1. void_charge: marks is_void=True, returns 200
# ---------------------------------------------------------------------------

def test_void_charge_marks_void_and_returns_200():
    sid, acct, user = _school_and_account()
    ch = _make_charge(sid, acct)
    c, kwargs = _auth_client(user, sid)

    resp = c.post(VOID_CHARGE_URL.format(ch.id), **kwargs)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"

    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["is_void"] is True

    ch.refresh_from_db()
    assert ch.is_void is True


# ---------------------------------------------------------------------------
# 2. void_charge: idempotent — second call also 200
# ---------------------------------------------------------------------------

def test_void_charge_is_idempotent():
    sid, acct, user = _school_and_account()
    ch = _make_charge(sid, acct)
    c, kwargs = _auth_client(user, sid)

    resp1 = c.post(VOID_CHARGE_URL.format(ch.id), **kwargs)
    assert resp1.status_code == 200

    resp2 = c.post(VOID_CHARGE_URL.format(ch.id), **kwargs)
    assert resp2.status_code == 200, f"Second void call failed: {resp2.status_code}: {resp2.content}"

    ch.refresh_from_db()
    assert ch.is_void is True


# ---------------------------------------------------------------------------
# 3. void_charge: removes allocations before voiding
# ---------------------------------------------------------------------------

def test_void_charge_removes_allocations():
    sid, acct, user = _school_and_account()
    ch = _make_charge(sid, acct, amount="200.00")
    pay = _make_payment(sid, acct, amount="200.00")
    Allocation.objects.create(school_id=sid, payment=pay, charge=ch, amount=Decimal("200.00"))
    assert Allocation.objects.filter(charge=ch).count() == 1

    c, kwargs = _auth_client(user, sid)
    resp = c.post(VOID_CHARGE_URL.format(ch.id), **kwargs)
    assert resp.status_code == 200

    assert Allocation.objects.filter(charge=ch).count() == 0, "Allocations should be deleted on void"


# ---------------------------------------------------------------------------
# 4. void_payment: marks is_void=True, returns 200
# ---------------------------------------------------------------------------

def test_void_payment_marks_void_and_returns_200():
    sid, acct, user = _school_and_account()
    pay = _make_payment(sid, acct)
    c, kwargs = _auth_client(user, sid)

    resp = c.post(VOID_PAYMENT_URL.format(pay.id), **kwargs)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"

    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["is_void"] is True

    pay.refresh_from_db()
    assert pay.is_void is True


# ---------------------------------------------------------------------------
# 5. void_payment: idempotent — second call also 200
# ---------------------------------------------------------------------------

def test_void_payment_is_idempotent():
    sid, acct, user = _school_and_account()
    pay = _make_payment(sid, acct)
    c, kwargs = _auth_client(user, sid)

    resp1 = c.post(VOID_PAYMENT_URL.format(pay.id), **kwargs)
    assert resp1.status_code == 200

    resp2 = c.post(VOID_PAYMENT_URL.format(pay.id), **kwargs)
    assert resp2.status_code == 200, f"Second void call failed: {resp2.status_code}: {resp2.content}"

    pay.refresh_from_db()
    assert pay.is_void is True


# ---------------------------------------------------------------------------
# 6. void_payment: removes allocations before voiding
# ---------------------------------------------------------------------------

def test_void_payment_removes_allocations():
    sid, acct, user = _school_and_account()
    ch = _make_charge(sid, acct, amount="150.00")
    pay = _make_payment(sid, acct, amount="150.00")
    Allocation.objects.create(school_id=sid, payment=pay, charge=ch, amount=Decimal("150.00"))
    assert Allocation.objects.filter(payment=pay).count() == 1

    c, kwargs = _auth_client(user, sid)
    resp = c.post(VOID_PAYMENT_URL.format(pay.id), **kwargs)
    assert resp.status_code == 200

    assert Allocation.objects.filter(payment=pay).count() == 0, "Allocations should be deleted on void"
