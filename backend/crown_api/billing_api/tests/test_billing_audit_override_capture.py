from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from billing.models import BillingAuditEvent
from core.models import School
from households.models import Household
from ledger.models import Charge, LedgerAccount, Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_finance_user():
    primary_school = School.objects.create(name="Primary School")
    override_school = School.objects.create(name="Override School")

    User = get_user_model()
    u = User.objects.create_user(username="staff_finance_user", password="pass12345!")
    u.is_staff = True
    u.save(update_fields=["is_staff"])

    if hasattr(u, "school_id"):
        setattr(u, "school_id", primary_school.id)
        u.save(update_fields=["school_id"])

    g, _ = Group.objects.get_or_create(name="Business Manager")
    u.groups.add(g)

    return u, primary_school, override_school


@pytest.fixture
def staff_finance_client(staff_finance_user):
    u, _, _ = staff_finance_user
    client = APIClient()
    client.force_authenticate(user=u)
    return client


def _seed_household_with_charge(school_id):
    hh = Household.objects.create(school_id=school_id, name="Household")
    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
    ch = Charge.objects.create(
        school_id=school_id,
        account=acct,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    return hh, acct, ch


def test_billing_audit_includes_school_override_id_on_record_payment(staff_finance_user, staff_finance_client):
    u, _primary_school, override_school = staff_finance_user

    hh, acct, ch = _seed_household_with_charge(override_school.id)

    payload = {
        "household_id": str(hh.id),
        "amount_cents": 5000,
        "method": "cash",
        "reference": "SMOKE-0102-OVERRIDE",
        "received_on": date.today().isoformat(),
        "allocations": [
            {"ledger_charge_id": str(ch.id), "amount_cents": 5000},
        ],
    }

    resp = staff_finance_client.post(
        "/api/billing/payments/record/",
        payload,
        format="json",
        HTTP_X_CROWN_SCHOOL_ID=str(override_school.id),
    )
    assert resp.status_code == 201

    payment_id = resp.data.get("payment_id")
    assert payment_id

    p = Payment.objects.get(id=payment_id)
    assert p.school_id == override_school.id
    assert p.account_id == acct.id

    audit = BillingAuditEvent.objects.filter(
        school_id=override_school.id,
        entity_type=BillingAuditEvent.ENTITY_PAYMENT,
        entity_id=p.id,
        action="PAYMENT_RECORDED",
    ).first()
    assert audit is not None
    assert audit.details_json.get("school_override_id") == str(override_school.id)
    assert audit.details_json.get("reference") == "SMOKE-0102-OVERRIDE"
