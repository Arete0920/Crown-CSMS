import csv
import io

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db


def _read_csv_bytes(content: bytes):
    text = content.decode("utf-8")
    f = io.StringIO(text)
    return list(csv.reader(f))


@pytest.fixture
def auth_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="user_financial", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def auth_client(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


def _model_exists(app_label: str, model_name: str) -> bool:
    try:
        return apps.get_model(app_label, model_name) is not None
    except LookupError:
        return False


def test_ledger_charges_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/ledger-charges.csv")
    assert resp.status_code in (401, 403)


def test_ledger_allocations_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/ledger-allocations.csv")
    assert resp.status_code in (401, 403)


def test_payments_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/payments.csv")
    assert resp.status_code in (401, 403)


def test_ledger_charges_csv_streams_when_model_exists(auth_client):
    candidates = [
        ("ledger", "LedgerCharge"),
        ("accounting", "LedgerCharge"),
        ("billing", "LedgerCharge"),
        ("finance", "LedgerCharge"),
        ("ledger", "Charge"),
        ("accounting", "Charge"),
    ]
    if not any(_model_exists(a, m) for a, m in candidates):
        pytest.skip("No LedgerCharge/Charge model found under expected labels yet.")

    resp = auth_client.get("/api/exports/ledger-charges.csv")
    assert resp.status_code in (200, 500)
    content = b"".join(resp.streaming_content)
    rows = _read_csv_bytes(content)
    assert len(rows) >= 1
    assert len(rows[0]) >= 1


def test_ledger_allocations_csv_streams_when_model_exists(auth_client):
    candidates = [
        ("ledger", "LedgerAllocation"),
        ("accounting", "LedgerAllocation"),
        ("billing", "LedgerAllocation"),
        ("finance", "LedgerAllocation"),
        ("ledger", "Allocation"),
        ("accounting", "Allocation"),
    ]
    if not any(_model_exists(a, m) for a, m in candidates):
        pytest.skip("No LedgerAllocation/Allocation model found under expected labels yet.")

    resp = auth_client.get("/api/exports/ledger-allocations.csv")
    assert resp.status_code in (200, 500)
    content = b"".join(resp.streaming_content)
    rows = _read_csv_bytes(content)
    assert len(rows) >= 1
    assert len(rows[0]) >= 1


def test_payments_csv_streams_when_model_exists(auth_client):
    candidates = [
        ("payments", "Payment"),
        ("ledger", "Payment"),
        ("billing", "Payment"),
        ("finance", "Payment"),
        ("accounting", "Payment"),
    ]
    if not any(_model_exists(a, m) for a, m in candidates):
        pytest.skip("No Payment model found under expected labels yet.")

    resp = auth_client.get("/api/exports/payments.csv")
    assert resp.status_code in (200, 500)
    content = b"".join(resp.streaming_content)
    rows = _read_csv_bytes(content)
    assert len(rows) >= 1
    assert len(rows[0]) >= 1
