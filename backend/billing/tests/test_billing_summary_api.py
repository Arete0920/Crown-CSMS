import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from billing.models import BillingRun, Invoice
from ledger.models import LedgerAccount, Charge, Payment
from ledger.models import Allocation as PaymentAllocation

pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_billing_run_summary_gross_aid_net():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")

    run = BillingRun.objects.create(school_id=school.id, term="2026-FALL", run_type="TUITION", description="Run", amount_per_student=Decimal("0.00"))
    inv = Invoice.objects.create(school_id=school.id, billing_run=run, household=hh, total_amount=Decimal("1000.00"))

    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)
    ch = Charge.objects.create(school_id=school.id, account=acct, description="Tuition", amount=Decimal("1000.00"))
    inv.ledger_charge_id = ch.id
    inv.save(update_fields=["ledger_charge_id"])

    aid = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("400.00"), source="FINANCIAL_AID", reference="award:x")
    PaymentAllocation.objects.create(school_id=school.id, payment=aid, charge=ch, amount=Decimal("400.00"))

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    resp = c.get(f"/api/v1/billing/runs/{run.id}/summary/")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert Decimal(data["gross_total"]) == Decimal("1000.00")
    assert Decimal(data["aid_applied_total"]) == Decimal("400.00")
    assert Decimal(data["net_due_total"]) == Decimal("600.00")
