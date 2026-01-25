from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from billing.models import BillingAuditEvent, BillingRun, Invoice
from core.models import School
from households.models import Household
from ledger.models import Allocation, Charge, LedgerAccount, Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def finance_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="finance_user", password="pass12345!")
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
    u = User.objects.create_user(username="non_finance_user", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def non_finance_client(non_finance_user):
    client = APIClient()
    client.force_authenticate(user=non_finance_user)
    return client


def _seed_invoice_with_charge(school_id):
    hh = Household.objects.create(school_id=school_id, name="Household")
    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
    ch = Charge.objects.create(
        school_id=school_id,
        account=acct,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    run = BillingRun.objects.create(school_id=school_id, term="2026-FALL", run_type="TUITION")
    inv = Invoice.objects.create(
        school_id=school_id,
        billing_run=run,
        household=hh,
        due_on=date.today(),
        total_amount=Decimal("100.00"),
        ledger_charge_id=ch.id,
    )
    return inv, acct, ch


def test_record_payment_requires_finance_role(non_finance_client):
    resp = non_finance_client.post(
        "/api/billing/payments/record/",
        {"invoice_id": "00000000-0000-0000-0000-000000000000", "amount_cents": 1000, "method": "cash", "reference": "R-1"},
        format="json",
    )
    assert resp.status_code == 403


def test_record_payment_creates_payment_allocation_and_audit(finance_user, finance_client):
    school_id = getattr(finance_user, "school_id")
    inv, acct, ch = _seed_invoice_with_charge(school_id)

    resp = finance_client.post(
        "/api/billing/payments/record/",
        {
            "invoice_id": str(inv.id),
            "amount_cents": 2500,
            "method": "cash",
            "reference": "R-ABC-001",
            "received_on": date.today().isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 201

    payment_id = resp.data.get("payment_id")
    assert payment_id

    p = Payment.objects.get(id=payment_id)
    assert p.school_id == school_id
    assert p.account_id == acct.id
    assert str(p.reference) == "R-ABC-001"
    assert str(p.amount) == "25.00"

    alloc = Allocation.objects.get(payment=p, charge=ch)
    assert str(alloc.amount) == "25.00"

    audit = BillingAuditEvent.objects.filter(
        school_id=school_id,
        entity_type=BillingAuditEvent.ENTITY_INVOICE,
        entity_id=inv.id,
        action="PAYMENT_RECORDED",
    ).first()
    assert audit is not None
    assert audit.details_json.get("payment_id") == str(p.id)


def test_record_payment_duplicate_reference_returns_409(finance_user, finance_client):
    school_id = getattr(finance_user, "school_id")
    inv, _, _ = _seed_invoice_with_charge(school_id)

    payload = {
        "invoice_id": str(inv.id),
        "amount_cents": 1000,
        "method": "cash",
        "reference": "R-DUPE-001",
    }

    r1 = finance_client.post("/api/billing/payments/record/", payload, format="json")
    assert r1.status_code == 201

    r2 = finance_client.post("/api/billing/payments/record/", payload, format="json")
    assert r2.status_code == 409
