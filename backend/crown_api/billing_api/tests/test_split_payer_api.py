import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from core.models import School
from households.models import Guardian, Household, Student
from billing.models import (
    BillingPayer,
    BillingResponsibilityRule,
    BillingRun,
    Invoice,
    InvoicePayerShare,
    PayerAllocationAttribution,
)
from ledger.models import Allocation, Charge, LedgerAccount, Payment


pytestmark = pytest.mark.django_db


def _user(school, group_name=None):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        password="pass12345!",
    )
    if hasattr(user, "school_id"):
        user.school_id = school.id
        user.save(update_fields=["school_id"])
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def _invoice(school, household, amount=Decimal("1000.00")):
    run = BillingRun.objects.create(
        school_id=school.id,
        term="2026-FALL",
        run_type="TUITION",
        amount_per_student=amount,
    )
    return Invoice.objects.create(
        school_id=school.id,
        household=household,
        billing_run=run,
        total_amount=amount,
    )


def test_finance_user_can_create_payer_and_responsibility_rule():
    school = School.objects.create(name="Split Payer API School")
    household = Household.objects.create(school_id=school.id, name="Family")
    finance = _user(school, "finance_admin")
    client = Client()
    client.force_login(finance)

    payer_resp = client.post(
        f"/api/v1/billing/households/{household.id}/payers/",
        data={
            "payer_type": "THIRD_PARTY",
            "display_name": "Supporting Grandparent",
            "email": "grandparent@example.org",
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert payer_resp.status_code == 201
    payer_id = payer_resp.json()["payer_id"]

    rule_resp = client.post(
        f"/api/v1/billing/households/{household.id}/responsibility-rules/",
        data={
            "payer_id": payer_id,
            "charge_type": "TUITION",
            "percentage_bps": 10000,
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert rule_resp.status_code == 201
    assert rule_resp.json()["configured_scope_bps"] == 10000
    assert BillingPayer.objects.filter(id=payer_id, household=household).exists()
    assert BillingResponsibilityRule.objects.filter(payer_id=payer_id, percentage_bps=10000).exists()


def test_nonfinance_user_cannot_configure_payers():
    school = School.objects.create(name="Split Payer Deny School")
    household = Household.objects.create(school_id=school.id, name="Family")
    user = _user(school, "admissions_team")
    client = Client()
    client.force_login(user)

    resp = client.post(
        f"/api/v1/billing/households/{household.id}/payers/",
        data={"payer_type": "THIRD_PARTY", "display_name": "Unauthorized"},
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert resp.status_code == 403


def test_payer_self_service_returns_only_authenticated_payer_share():
    school = School.objects.create(name="Payer Privacy School")
    household = Household.objects.create(school_id=school.id, name="Family")
    parent_a = _user(school)
    parent_b = _user(school)
    guardian_a = Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent_a,
        first_name="Parent",
        last_name="A",
        email="a@example.org",
    )
    guardian_b = Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent_b,
        first_name="Parent",
        last_name="B",
        email="b@example.org",
    )
    payer_a = BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        guardian=guardian_a,
        account=parent_a,
        payer_type=BillingPayer.PayerType.GUARDIAN,
        display_name="Parent A",
    )
    payer_b = BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        guardian=guardian_b,
        account=parent_b,
        payer_type=BillingPayer.PayerType.GUARDIAN,
        display_name="Parent B",
    )
    invoice = _invoice(school, household)
    InvoicePayerShare.objects.create(
        school_id=school.id, invoice=invoice, payer=payer_a, amount=Decimal("600.00")
    )
    InvoicePayerShare.objects.create(
        school_id=school.id, invoice=invoice, payer=payer_b, amount=Decimal("400.00")
    )

    client = Client()
    client.force_login(parent_a)
    resp = client.get(
        "/api/v1/billing/my-payer-shares/",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["assigned_amount"] == "600.00"
    response_text = str(resp.json())
    assert "400.00" not in response_text
    assert "b@example.org" not in response_text


def test_payer_attribution_cannot_exceed_share_balance():
    school = School.objects.create(name="Payer Attribution School")
    household = Household.objects.create(school_id=school.id, name="Family")
    finance = _user(school, "finance_admin")
    payer = BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        payer_type=BillingPayer.PayerType.THIRD_PARTY,
        display_name="Sponsor",
    )
    invoice = _invoice(school, household, Decimal("100.00"))
    account = LedgerAccount.objects.create(school_id=school.id, household=household)
    charge = Charge.objects.create(
        school_id=school.id,
        account=account,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    invoice.ledger_charge_id = charge.id
    invoice.save(update_fields=["ledger_charge_id"])
    share = InvoicePayerShare.objects.create(
        school_id=school.id,
        invoice=invoice,
        payer=payer,
        amount=Decimal("60.00"),
    )
    payment = Payment.objects.create(
        school_id=school.id,
        account=account,
        amount=Decimal("100.00"),
        source="MANUAL",
        reference="payer-attr",
    )
    allocation = Allocation.objects.create(
        school_id=school.id,
        payment=payment,
        charge=charge,
        amount=Decimal("100.00"),
    )

    client = Client()
    client.force_login(finance)
    resp = client.post(
        "/api/v1/billing/payer-attributions/",
        data={
            "share_id": str(share.id),
            "allocation_id": str(allocation.id),
            "amount_cents": 7000,
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert resp.status_code == 400
    assert PayerAllocationAttribution.objects.count() == 0

    ok = client.post(
        "/api/v1/billing/payer-attributions/",
        data={
            "share_id": str(share.id),
            "allocation_id": str(allocation.id),
            "amount_cents": 6000,
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert ok.status_code == 201
    assert PayerAllocationAttribution.objects.get().amount == Decimal("60.00")
