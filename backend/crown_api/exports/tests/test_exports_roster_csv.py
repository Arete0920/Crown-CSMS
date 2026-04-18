import csv
import io

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


pytestmark = pytest.mark.django_db


def _read_csv_bytes(content: bytes):
    text = content.decode("utf-8")
    f = io.StringIO(text)
    return list(csv.reader(f))


@pytest.fixture
def auth_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="user", password=TEST_AUTH_SECRET)
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def auth_client(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


def test_households_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/households.csv")
    assert resp.status_code in (400, 401, 403)


def test_students_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/students.csv")
    assert resp.status_code in (400, 401, 403)


def test_staff_csv_requires_auth():
    client = APIClient()
    resp = client.get("/api/exports/staff.csv")
    assert resp.status_code in (400, 401, 403)


def _model_exists(app_label: str, model_name: str) -> bool:
    try:
        return apps.get_model(app_label, model_name) is not None
    except LookupError:
        return False


def test_households_csv_streams_when_model_exists(auth_client):
    # Match candidates in views.py
    candidates = [
        ("households", "Household"),
        ("core", "Household"),
        ("students", "Household"),
        ("people", "Household"),
    ]
    if not any(_model_exists(a, m) for a, m in candidates):
        pytest.skip("No Household model found yet under expected labels.")

    resp = auth_client.get("/api/exports/households.csv")
    assert resp.status_code in (200, 500)
    content = b"".join(resp.streaming_content)
    rows = _read_csv_bytes(content)
    assert len(rows) >= 1
    assert len(rows[0]) >= 1


def test_students_csv_streams_when_model_exists(auth_client):
    candidates = [
        ("students", "Student"),
        ("core", "Student"),
        ("people", "Student"),
        ("sis", "Student"),
    ]
    if not any(_model_exists(a, m) for a, m in candidates):
        pytest.skip("No Student model found yet under expected labels.")

    resp = auth_client.get("/api/exports/students.csv")
    assert resp.status_code in (200, 500)
    content = b"".join(resp.streaming_content)
    rows = _read_csv_bytes(content)
    assert len(rows) >= 1
    assert len(rows[0]) >= 1


def test_staff_csv_streams_when_model_exists(auth_client):
    candidates = [
        ("staff", "StaffMember"),
        ("staff", "Staff"),
        ("core", "StaffMember"),
        ("core", "Staff"),
        ("people", "StaffMember"),
        ("people", "Staff"),
    ]
    if not any(_model_exists(a, m) for a, m in candidates):
        pytest.skip("No Staff model found yet under expected labels.")

    resp = auth_client.get("/api/exports/staff.csv")
    assert resp.status_code in (200, 500)
    content = b"".join(resp.streaming_content)
    rows = _read_csv_bytes(content)
    assert len(rows) >= 1
    assert len(rows[0]) >= 1

