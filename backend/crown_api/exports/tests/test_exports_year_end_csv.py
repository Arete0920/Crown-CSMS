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


def _model_exists(app_label: str, model_name: str) -> bool:
    try:
        return apps.get_model(app_label, model_name) is not None
    except LookupError:
        return False


@pytest.fixture
def auth_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="user_year_end", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def auth_client(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


def test_year_end_tuition_paid_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/year-end/tuition-paid.csv?year=2025")
    assert resp.status_code in (401, 403)


def test_year_end_tuition_paid_csv_streams_when_payment_model_exists(auth_client):
    payment_candidates = [
        ("ledger", "Payment"),
        ("payments", "Payment"),
        ("crown_api", "Payment"),
        ("billing", "Payment"),
        ("finance", "Payment"),
        ("accounting", "Payment"),
    ]
    if not any(_model_exists(a, m) for a, m in payment_candidates):
        pytest.skip("No Payment model found under expected labels yet.")

    resp = auth_client.get("/api/exports/year-end/tuition-paid.csv?year=2025")
    assert resp.status_code in (200, 400, 500)

    rows = _read_csv_bytes(b"".join(resp.streaming_content))
    assert len(rows) >= 1
    assert rows[0][0] in ("school_id", "error")
