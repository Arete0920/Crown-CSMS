import csv
import io
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from core.models import School
from payments.authority_services import create_payment


pytestmark = pytest.mark.django_db


def _user(school, *, finance=False):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"finance-export-{uuid.uuid4()}",
        password="pass12345!",
        is_staff=finance,
    )
    if hasattr(user, "school_id"):
        user.school_id = school.id
        user.save(update_fields=["school_id"])
    group, _ = Group.objects.get_or_create(name="finance_admin" if finance else "parent")
    user.groups.add(group)
    return user


def _rows(response):
    text = b"".join(response.streaming_content).decode() if getattr(response, "streaming", False) else response.content.decode()
    return list(csv.DictReader(io.StringIO(text)))


def test_finance_handoff_export_is_school_scoped_and_reconciles_control_totals():
    school = School.objects.create(name="Finance Export School")
    foreign_school = School.objects.create(name="Foreign Finance Export School")
    user = _user(school, finance=True)

    own = create_payment(
        school_id=school.id,
        amount_cents=12_345,
        idempotency_key="export-own-payment",
    )
    foreign = create_payment(
        school_id=foreign_school.id,
        amount_cents=99_999,
        idempotency_key="export-foreign-payment",
    )

    client = Client()
    client.force_login(user)
    response = client.get(
        "/api/v1/payments/exports/finance-handoff.csv",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert response.status_code == 200
    rows = _rows(response)
    payment_rows = [row for row in rows if row["section"] == "payment_register"]
    assert [row["record_id"] for row in payment_rows] == [str(own.id)]
    assert str(foreign.id) not in {row["record_id"] for row in rows}

    totals = {
        row["record_id"]: row["amount"]
        for row in rows
        if row["section"] == "control_total"
    }
    assert totals["canonical_payment_total"] == "123.45"
    assert totals["settled_refund_total"] == "0.00"
    assert totals["net_canonical_cash"] == "123.45"

    journal_control = next(
        row for row in rows
        if row["section"] == "control_assertion" and row["record_id"] == "journal_balanced"
    )
    assert journal_control["status"] == "PASS"


def test_finance_handoff_export_rejects_nonfinance_role():
    school = School.objects.create(name="Finance Export Access School")
    user = _user(school, finance=False)
    client = Client()
    client.force_login(user)

    response = client.get(
        "/api/v1/payments/exports/finance-handoff.csv",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert response.status_code == 403
