import csv
import io
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from billing.models import BillingRun, Invoice, InstallmentPlan, InstallmentScheduleItem
from core.models import School
from households.models import Household
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


pytestmark = pytest.mark.django_db


def _read_csv_bytes(content: bytes):
    text = content.decode("utf-8")
    f = io.StringIO(text)
    return list(csv.reader(f))


@pytest.fixture
def finance_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="user", password=TEST_AUTH_SECRET)
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
    u = User.objects.create_user(username="user_non_finance", password=TEST_AUTH_SECRET)
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def non_finance_client(non_finance_user):
    client = APIClient()
    client.force_authenticate(user=non_finance_user)
    return client


def test_exports_invoices_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/invoices.csv")
    assert resp.status_code in (400, 401, 403)


def test_exports_installment_schedule_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/installment-schedule.csv")
    assert resp.status_code in (400, 401, 403)


def test_exports_invoices_csv_requires_finance_role(non_finance_client):
    resp = non_finance_client.get("/api/exports/invoices.csv")
    assert resp.status_code == 403


def test_exports_installment_schedule_csv_requires_finance_role(non_finance_client):
    resp = non_finance_client.get("/api/exports/installment-schedule.csv")
    assert resp.status_code == 403


def test_exports_invoices_csv_headers_and_rows(finance_user, finance_client):
    # Create a minimal invoice in-scope for the user's school
    school_id = getattr(finance_user, "school_id")
    hh = Household.objects.create(school_id=school_id, name="Household")
    run = BillingRun.objects.create(school_id=school_id, term="2026-FALL", run_type="TUITION")

    inv = Invoice.objects.create(
        school_id=school_id,
        billing_run=run,
        household=hh,
        due_on=date.today(),
        total_amount=Decimal("100.00"),
    )

    resp = finance_client.get("/api/exports/invoices.csv")
    assert resp.status_code == 200

    rows = _read_csv_bytes(b"".join(resp.streaming_content))
    assert len(rows) >= 2
    header = rows[0]
    assert header[:5] == ["invoice_id", "household_id", "due_on", "issued_on", "status"]

    found = any(r and r[0] == str(inv.id) for r in rows[1:])
    assert found


def test_exports_installment_schedule_csv_headers_and_rows(finance_user, finance_client):
    school_id = getattr(finance_user, "school_id")
    hh = Household.objects.create(school_id=school_id, name="Household")

    plan = InstallmentPlan.objects.create(
        school_id=school_id,
        term="2026-FALL",
        name="3-pay",
        installment_count=3,
        first_due_on=date.today(),
        cadence_days=30,
    )

    item = InstallmentScheduleItem.objects.create(
        school_id=school_id,
        plan=plan,
        household=hh,
        sequence=1,
        due_on=date.today(),
        amount=Decimal("250.00"),
    )

    resp = finance_client.get("/api/exports/installment-schedule.csv")
    assert resp.status_code == 200

    rows = _read_csv_bytes(b"".join(resp.streaming_content))
    assert len(rows) >= 2
    header = rows[0]
    assert header[:5] == ["schedule_item_id", "plan_id", "household_id", "due_on", "amount"]

    found = any(r and r[0] == str(item.id) for r in rows[1:])
    assert found

