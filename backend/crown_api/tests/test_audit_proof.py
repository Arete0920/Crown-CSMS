# backend/crown_api/tests/test_audit_proof.py
import uuid
from types import SimpleNamespace

import pytest
from django.test import Client, RequestFactory
from django.utils import timezone

from crown_api.audit import audit_log
from crown_api.audit_models import AuditEvent
from crown_api.auth_models import CrownUser
from crown_api.jwt_utils import build_access_token


pytestmark = pytest.mark.django_db


def _authenticated_client(*, role="admin", school_id=None):
    user = CrownUser.objects.create(
        email=f"{role}-{uuid.uuid4()}@example.test",
        password_hash="unused",
        role=role,
        school_id=school_id,
        is_active=True,
    )
    token = build_access_token(
        user_id=str(user.id),
        email=user.email,
        role=role,
        school_id=str(school_id) if school_id else None,
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {token}")


def test_audit_recent_forbidden_without_role():
    response = Client().get("/api/system/audit/recent/")
    assert response.status_code == 403
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "Forbidden"


def test_audit_recent_rejects_anonymous_demo_header(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    response = Client(HTTP_X_DEMO_ROLE="admin").get("/api/system/audit/recent/")
    assert response.status_code == 403
    assert response.json()["actual_role"] is None


def test_audit_recent_requires_authenticated_tenant_context():
    response = _authenticated_client(role="admin").get("/api/system/audit/recent/")
    assert response.status_code == 403
    assert response.json() == {"ok": False, "error": "Tenant context required"}


def test_audit_recent_allows_authenticated_admin_for_own_school():
    school_id = uuid.uuid4()
    response = _authenticated_client(role="admin", school_id=school_id).get(
        "/api/system/audit/recent/"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "results" in body


def test_audit_recent_allows_authenticated_finance_for_own_school():
    school_id = uuid.uuid4()
    response = _authenticated_client(role="finance", school_id=school_id).get(
        "/api/system/audit/recent/"
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_audit_recent_rejects_authenticated_wrong_role():
    school_id = uuid.uuid4()
    response = _authenticated_client(role="teacher", school_id=school_id).get(
        "/api/system/audit/recent/"
    )
    assert response.status_code == 403
    assert response.json()["actual_role"] == "teacher"


def test_audit_recent_filters_events_to_authenticated_school():
    school_id = uuid.uuid4()
    other_school_id = uuid.uuid4()
    included = AuditEvent.objects.create(
        school_id=school_id,
        actor_role="admin",
        action="tenant.included",
    )
    AuditEvent.objects.create(
        school_id=other_school_id,
        actor_role="admin",
        action="tenant.excluded",
    )

    response = _authenticated_client(
        role="finance",
        school_id=school_id,
    ).get("/api/system/audit/recent/?limit=10")

    assert response.status_code == 200
    results = response.json()["results"]
    assert [row["id"] for row in results] == [str(included.id)]
    assert all(row["school_id"] == str(school_id) for row in results)


def test_audit_recent_denies_cross_school_header_override():
    principal_school_id = uuid.uuid4()
    requested_school_id = uuid.uuid4()
    AuditEvent.objects.create(
        school_id=requested_school_id,
        actor_role="admin",
        action="tenant.private",
    )

    response = _authenticated_client(
        role="finance",
        school_id=principal_school_id,
    ).get(
        "/api/system/audit/recent/?limit=10",
        HTTP_X_SCHOOL_ID=str(requested_school_id),
    )

    assert response.status_code == 404
    assert response.json() == {"ok": False, "error": "Not found"}


def test_audit_log_creates_event_and_recent_returns_it():
    school_id = uuid.uuid4()
    client = _authenticated_client(school_id=school_id)

    request_factory = RequestFactory()
    request = request_factory.get("/x", HTTP_X_SCHOOL_ID=str(school_id))

    first_timestamp = timezone.now() - timezone.timedelta(seconds=20)
    second_timestamp = timezone.now() - timezone.timedelta(seconds=10)

    first_event = AuditEvent.objects.create(
        ts=first_timestamp,
        school_id=school_id,
        actor_role="admin",
        action="seed.one",
        object_type="student",
        object_id=uuid.uuid4(),
        meta={"n": 1},
    )
    audit_log(
        request=request,
        action="seed.two",
        object_type="invoice",
        object_id=uuid.uuid4(),
        meta={"n": 2},
    )
    second_event = AuditEvent.objects.get(action="seed.two")
    second_event.ts = second_timestamp
    second_event.save(update_fields=["ts"])

    response = client.get("/api/system/audit/recent/?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["count"] >= 2

    results = body["results"]
    assert results[0]["action"] == "seed.two"
    assert results[1]["action"] == "seed.one"
    assert results[1]["id"] == str(first_event.id)


def test_audit_log_prefers_authorized_canonical_tenant_over_raw_header():
    request_factory = RequestFactory()
    authorized_school_id = uuid.uuid4()
    conflicting_header_id = uuid.uuid4()
    request = request_factory.get("/x", HTTP_X_SCHOOL_ID=str(conflicting_header_id))
    request.crown_tenant = SimpleNamespace(school_id=authorized_school_id)

    event = audit_log(request=request, action="tenant.authorized")
    assert event.school_id == authorized_school_id


def test_audit_log_supports_compatibility_tenant_school_id_without_header():
    request_factory = RequestFactory()
    school_id = uuid.uuid4()
    request = request_factory.get("/x")
    request.tenant_school_id = school_id

    event = audit_log(request=request, action="tenant.compatibility")
    assert event.school_id == school_id


def test_audit_log_falls_back_to_header_for_unbound_legacy_request():
    request_factory = RequestFactory()
    school_id = uuid.uuid4()
    request = request_factory.get("/x", HTTP_X_SCHOOL_ID=str(school_id))

    event = audit_log(request=request, action="tenant.legacy")
    assert event.school_id == school_id
