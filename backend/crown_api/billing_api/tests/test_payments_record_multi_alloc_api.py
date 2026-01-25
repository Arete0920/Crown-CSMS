from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from core.models import School
from households.models import Household
from ledger.models import Allocation, Charge, LedgerAccount, Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def finance_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="finance_user_multi", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])

    g, _ = Group.objects.get_or_create(name="Business Manager")
    u.groups.add(g)
    return u


@pytest.fixture
def finance_client(finance_user):
    client = APIClient()
    client.force_authenticate(user=finance_user)
    return client


@pytest.fixture
def non_finance_user():
    school = School.objects.create(name="Test School 2")
    User = get_user_model()
    u = User.objects.create_user(username="non_finance_user_multi", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def non_finance_client(non_finance_user):
    client = APIClient()
    client.force_authenticate(user=non_finance_user)
    return client


def _seed_household_with_two_charges(school_id):
    hh = Household.objects.create(school_id=school_id, name="Household")
    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
    ch1 = Charge.objects.create(
        school_id=school_id,
        account=acct,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    ch2 = Charge.objects.create(
        school_id=school_id,
        account=acct,
        description="Fees",
        amount=Decimal("50.00"),
    )
    return hh, acct, ch1, ch2


def test_record_payment_multi_allocation_201(finance_user, finance_client):
    school_id = getattr(finance_user, "school_id")
    hh, acct, ch1, ch2 = _seed_household_with_two_charges(school_id)

    payload = {
        "household_id": str(hh.id),
        "amount_cents": 12345,
        "method": "check",
        "reference": "R-MULTI-001",
        "received_on": date.today().isoformat(),
        "allocations": [
            {"ledger_charge_id": str(ch1.id), "amount_cents": 5000},
            {"ledger_charge_id": str(ch2.id), "amount_cents": 7345},
        ],
    }

    resp = finance_client.post("/api/billing/payments/record/", payload, format="json")
    assert resp.status_code == 201

    payment_id = resp.data.get("payment_id")
    assert payment_id

    p = Payment.objects.get(id=payment_id)
    assert p.school_id == school_id
    assert p.account_id == acct.id
    assert p.reference == "R-MULTI-001"
    assert str(p.amount) == "123.45"

    allocs = list(Allocation.objects.filter(payment=p).order_by("charge_id"))
    assert len(allocs) == 2
    assert {a.charge_id for a in allocs} == {ch1.id, ch2.id}


def test_record_payment_multi_allocation_sum_mismatch_400(finance_user, finance_client):
    school_id = getattr(finance_user, "school_id")
    hh, _, ch1, ch2 = _seed_household_with_two_charges(school_id)

    payload = {
        "household_id": str(hh.id),
        "amount_cents": 10000,
        "method": "cash",
        "reference": "R-MULTI-002",
        "allocations": [
            {"ledger_charge_id": str(ch1.id), "amount_cents": 5000},
            {"ledger_charge_id": str(ch2.id), "amount_cents": 4000},
        ],
    }

    resp = finance_client.post("/api/billing/payments/record/", payload, format="json")
    assert resp.status_code == 400


def test_record_payment_multi_allocation_requires_finance_role_403(non_finance_client):
    resp = non_finance_client.post(
        "/api/billing/payments/record/",
        {
            "household_id": "00000000-0000-0000-0000-000000000000",
            "amount_cents": 1000,
            "method": "cash",
            "reference": "R-MULTI-003",
            "allocations": [
                {
                    "ledger_charge_id": "00000000-0000-0000-0000-000000000000",
                    "amount_cents": 1000,
                }
            ],
        },
        format="json",
    )
    assert resp.status_code == 403


def test_record_payment_multi_allocation_duplicate_reference_409(finance_user, finance_client):
    school_id = getattr(finance_user, "school_id")
    hh, _, ch1, ch2 = _seed_household_with_two_charges(school_id)

    payload = {
        "household_id": str(hh.id),
        "amount_cents": 2000,
        "method": "cash",
        "reference": "R-MULTI-DUPE",
        "allocations": [
            {"ledger_charge_id": str(ch1.id), "amount_cents": 1000},
            {"ledger_charge_id": str(ch2.id), "amount_cents": 1000},
        ],
    }

    r1 = finance_client.post("/api/billing/payments/record/", payload, format="json")
    assert r1.status_code == 201

    r2 = finance_client.post("/api/billing/payments/record/", payload, format="json")
    assert r2.status_code == 409
