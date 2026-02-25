"""
Phase 2 Priority 2 – Ledger Invariant endpoint proof tests.

Invariants checked by GET /api/v1/ledger/invariants/:
  1. over_allocated  – allocations exceed charge face value
  2. negative_charges – non-void charges with amount < 0
  3. negative_payments – non-void payments with amount < 0

All tests are self-contained; no seed command required.
"""
import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School, UserRole
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment, Allocation
from ledger.services import allocate_payment_fifo

pytestmark = pytest.mark.django_db

URL = "/api/v1/ledger/invariants/"


def _school_and_user():
    """Return (school_id, user) for a fresh school. User is granted HEAD_OF_SCHOOL."""
    sid = uuid.uuid4()
    school = School.objects.get_or_create(id=sid, defaults={"name": f"School-{sid}"})[0]
    User = get_user_model()
    user = User.objects.create_user(username=f"u-{uuid.uuid4()}", password="pass12345!")
    if hasattr(user, "school_id"):
        user.school_id = sid
        user.save(update_fields=["school_id"])
    UserRole.objects.create(school_id=sid, user=user, role_code="HEAD_OF_SCHOOL")
    return sid, user


def _make_account(sid):
    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
    return LedgerAccount.objects.create(school_id=sid, household=hh)


# ---------------------------------------------------------------------------
# Test 1: unauthenticated request is rejected (no 2xx)
# ---------------------------------------------------------------------------

def test_invariants_unauthenticated_rejected():
    c = Client()
    resp = c.get(URL)
    assert resp.status_code not in (200, 201, 204), (
        f"Expected auth rejection, got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Test 2: authenticated, no seed violations → 200 + clean=True
# ---------------------------------------------------------------------------

def test_invariants_clean_ledger_returns_clean():
    sid, user = _school_and_user()
    acct = _make_account(sid)

    # A 100.00 charge with a perfectly-matched 100.00 allocation
    charge = Charge.objects.create(school_id=sid, account=acct, description="Tuition", amount=Decimal("100.00"))
    payment = Payment.objects.create(school_id=sid, account=acct, amount=Decimal("100.00"))
    Allocation.objects.create(school_id=sid, payment=payment, charge=charge, amount=Decimal("100.00"))

    c = Client()
    c.force_login(user)
    resp = c.get(URL, HTTP_X_SCHOOL_ID=str(sid))

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["clean"] is True
    assert data["data"]["violations"]["over_allocated"] == []
    assert data["data"]["violations"]["negative_charges"] == []
    assert data["data"]["violations"]["negative_payments"] == []
    assert data["data"]["school_id"] == str(sid)


# ---------------------------------------------------------------------------
# Test 3: over-allocation is detected + tenant isolation
# ---------------------------------------------------------------------------

def test_invariants_detects_over_allocation():
    sid, user = _school_and_user()
    acct = _make_account(sid)

    charge = Charge.objects.create(school_id=sid, account=acct, description="Fee", amount=Decimal("100.00"))
    payment = Payment.objects.create(school_id=sid, account=acct, amount=Decimal("999.00"))
    # Allocated 150 against a 100-face charge → over by 50
    Allocation.objects.create(school_id=sid, payment=payment, charge=charge, amount=Decimal("150.00"))

    c = Client()
    c.force_login(user)
    resp = c.get(URL, HTTP_X_SCHOOL_ID=str(sid))

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["clean"] is False
    violations = body["data"]["violations"]["over_allocated"]
    assert len(violations) == 1
    assert violations[0]["charge_id"] == str(charge.id)
    assert Decimal(violations[0]["overage"]) == Decimal("50.00")


# ---------------------------------------------------------------------------
# Test 4: tenant isolation — other school's violations invisible
# ---------------------------------------------------------------------------

def test_invariants_tenant_isolation():
    """
    school_a has an over-allocated charge.
    school_b has a clean ledger.
    school_b's user must see clean=True (no cross-tenant bleed).
    """
    sid_a, _ = _school_and_user()
    sid_b, user_b = _school_and_user()

    # Pollute school_a
    acct_a = _make_account(sid_a)
    charge_a = Charge.objects.create(school_id=sid_a, account=acct_a, description="Bad charge", amount=Decimal("50.00"))
    pay_a = Payment.objects.create(school_id=sid_a, account=acct_a, amount=Decimal("999.00"))
    Allocation.objects.create(school_id=sid_a, payment=pay_a, charge=charge_a, amount=Decimal("200.00"))

    # school_b is clean
    acct_b = _make_account(sid_b)
    Charge.objects.create(school_id=sid_b, account=acct_b, description="Normal", amount=Decimal("300.00"))

    c = Client()
    c.force_login(user_b)
    resp = c.get(URL, HTTP_X_SCHOOL_ID=str(sid_b))

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["school_id"] == str(sid_b)
    assert body["data"]["clean"] is True
    assert body["data"]["violations"]["over_allocated"] == []


# ---------------------------------------------------------------------------
# Test 5: service rejects cross-tenant allocation (payment school_a, arg school_b)
# ---------------------------------------------------------------------------

def test_allocation_cross_tenant_guard():
    """allocate_payment_fifo raises ValueError when payment.school_id != school_id arg."""
    sid_a, _ = _school_and_user()
    sid_b, _ = _school_and_user()
    acct_a = _make_account(sid_a)
    payment_a = Payment.objects.create(
        school_id=sid_a, account=acct_a, amount=Decimal("100.00")
    )

    with pytest.raises(ValueError, match="school_id mismatch"):
        allocate_payment_fifo(school_id=sid_b, payment=payment_a)


# ---------------------------------------------------------------------------
# Test 6: FIFO allocator skips voided charges (is_void=True)
# ---------------------------------------------------------------------------

def test_allocation_on_voided_charge_skipped():
    """allocate_payment_fifo must not allocate against a voided charge."""
    sid, _ = _school_and_user()
    acct = _make_account(sid)

    charge = Charge.objects.create(
        school_id=sid, account=acct, description="Void Fee", amount=Decimal("100.00")
    )
    # Void the charge (triggers reversal JE signal, which is fine)
    charge.is_void = True
    charge.save(update_fields=["is_void"])

    payment = Payment.objects.create(
        school_id=sid, account=acct, amount=Decimal("100.00")
    )

    result = allocate_payment_fifo(school_id=sid, payment=payment)

    assert result.allocations_created == 0, (
        "FIFO allocator must skip voided charges; allocations_created must be 0"
    )
    assert Allocation.objects.filter(payment=payment).count() == 0, (
        "No Allocation rows should exist for a payment against only voided charges"
    )
