import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from ledger.tests.factories import grant_finance_authority
from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment, Allocation


pytestmark = pytest.mark.django_db

TEST_AUTH_SECRET = "testpass"


def _mk_user_with_school_id(school_id):
    School.objects.get_or_create(id=school_id, defaults={"name": f"School-{school_id}"})
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password=TEST_AUTH_SECRET)
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school_id)
        u.save(update_fields=["school_id"])
    grant_finance_authority(u, school_id)
    return u


def test_record_payment_strict_allocation_sum_and_creates_allocations():
    school_id = uuid.uuid4()
    School.objects.create(id=school_id, name="Test School")
    hh = Household.objects.create(school_id=school_id, name="HH")
    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)

    ch1 = Charge.objects.create(school_id=school_id, account=acct, description="Tuition", amount=Decimal("150.00"))
    ch2 = Charge.objects.create(school_id=school_id, account=acct, description="Fees", amount=Decimal("100.00"))

    user = _mk_user_with_school_id(school_id)
    c = Client()
    c.force_login(user)

    payload = {
        "household_id": str(hh.id),
        "account_id": str(acct.id),
        "payment_date": "2026-01-25",
        "amount": "250.00",
        "reference": "CHK-1042",
        "source": "manual",
        "allocations": [
            {"charge_id": str(ch1.id), "amount": "150.00"},
            {"charge_id": str(ch2.id), "amount": "100.00"},
        ],
    }

    resp = c.post("/api/v1/ledger/payments/", data=payload, content_type="application/json")
    assert resp.status_code == 201

    assert Payment.objects.filter(school_id=school_id, account=acct).count() == 1
    p = Payment.objects.get(school_id=school_id, account=acct)
    assert p.source == "manual"
    assert p.reference == "CHK-1042"

    assert Allocation.objects.filter(payment=p).count() == 2


def test_record_payment_rejects_sum_mismatch_by_default():
    school_id = uuid.uuid4()
    School.objects.create(id=school_id, name="Test School")
    hh = Household.objects.create(school_id=school_id, name="HH")
    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
    ch1 = Charge.objects.create(school_id=school_id, account=acct, description="Tuition", amount=Decimal("150.00"))

    user = _mk_user_with_school_id(school_id)
    c = Client()
    c.force_login(user)

    payload = {
        "account_id": str(acct.id),
        "amount": "250.00",
        "allocations": [{"charge_id": str(ch1.id), "amount": "100.00"}],
    }

    resp = c.post("/api/v1/ledger/payments/", data=payload, content_type="application/json")
    assert resp.status_code == 400


def test_open_charges_lists_remaining_balances():
    school_id = uuid.uuid4()
    School.objects.create(id=school_id, name="Test School")
    hh = Household.objects.create(school_id=school_id, name="HH")
    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)

    ch1 = Charge.objects.create(school_id=school_id, account=acct, description="Tuition", amount=Decimal("150.00"))

    user = _mk_user_with_school_id(school_id)
    c = Client()
    c.force_login(user)

    resp = c.get(f"/api/v1/ledger/charges/open/?household_id={hh.id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["charge"]["id"] == str(ch1.id)

