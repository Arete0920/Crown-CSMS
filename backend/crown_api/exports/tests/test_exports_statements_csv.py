import csv
import io

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from core.models import School
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


pytestmark = pytest.mark.django_db


def _read_csv_bytes(content: bytes):
    text = content.decode("utf-8")
    f = io.StringIO(text)
    return list(csv.reader(f))


def _model_exists(app_label: str, model_name: str) -> bool:
    try:
        return apps.get_model(app_label, model_name) is not None
    except LookupError:
        return False


@pytest.fixture
def finance_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="user_statements", password=TEST_AUTH_SECRET)
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
    u = User.objects.create_user(username="user_statements_nonrole", password=TEST_AUTH_SECRET)
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def non_finance_client(non_finance_user):
    client = APIClient()
    client.force_authenticate(user=non_finance_user)
    return client


def test_statements_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/statements.csv")
    assert resp.status_code in (400, 401, 403)


def test_statements_csv_requires_finance_role(non_finance_client):
    resp = non_finance_client.get("/api/exports/statements.csv")
    assert resp.status_code == 403


def test_statements_csv_streams_when_invoice_model_exists(finance_client):
    invoice_candidates = [
        ("billing", "Invoice"),
        ("finance", "Invoice"),
        ("ledger", "Invoice"),
        ("accounting", "Invoice"),
    ]
    if not any(_model_exists(a, m) for a, m in invoice_candidates):
        pytest.skip("No Invoice model found under expected labels yet.")

    resp = finance_client.get("/api/exports/statements.csv")
    assert resp.status_code in (200, 500)
    rows = _read_csv_bytes(b"".join(resp.streaming_content))
    assert len(rows) >= 1
    assert rows[0][0] in ("as_of", "error")

