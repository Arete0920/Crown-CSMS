# backend/crown_api/tests/test_audit_proof.py
import uuid
from types import SimpleNamespace

import pytest
from django.test import Client, RequestFactory
from django.utils import timezone

from crown_api.audit import audit_log
from crown_api.audit_models import AuditEvent


pytestmark = pytest.mark.django_db


def _make_admin_client(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    return Client(HTTP_X_DEMO_ROLE="admin")


def test_audit_recent_forbidden_without_role():
    c = Client()
    resp = c.get("/api/system/audit/recent/")
    assert resp.status_code == 403
    body = resp.json()
    assert body["ok"] is False
    assert body["error"] == "Forbidden"


def test_audit_recent_allows_admin_via_demo_header(monkeypatch):
    c = _make_admin_client(monkeypatch)
    resp = c.get("/api/system/audit/recent/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "results" in body


def test_audit_log_creates_event_and_recent_returns_it(monkeypatch):
    c = _make_admin_client(monkeypatch)

    rf = RequestFactory()
    school_id = uuid.uuid4()
    req = rf.get("/x", **{"HTTP_X_SCHOOL_ID": str(school_id), "HTTP_X_DEMO_ROLE": "admin"})

    # deterministic ordering via explicit timestamps
    t1 = timezone.now() - timezone.timedelta(seconds=20)
    t2 = timezone.now() - timezone.timedelta(seconds=10)

    e1 = AuditEvent.objects.create(
        ts=t1,
        school_id=school_id,
        actor_role="admin",
        action="seed.one",
        object_type="student",
        object_id=uuid.uuid4(),
        meta={"n": 1},
    )
    audit_log(
        request=req,
        action="seed.two",
        object_type="invoice",
        object_id=uuid.uuid4(),
        meta={"n": 2},
    )
    # force ts for deterministic order
    e2 = AuditEvent.objects.get(action="seed.two")
    e2.ts = t2
    e2.save(update_fields=["ts"])

    resp = c.get("/api/system/audit/recent/?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["count"] >= 2

    results = body["results"]
    assert results[0]["action"] == "seed.two"
    assert results[1]["action"] == "seed.one"
    assert results[1]["id"] == str(e1.id)


def test_audit_log_prefers_authorized_canonical_tenant_over_raw_header():
    rf = RequestFactory()
    authorized_school_id = uuid.uuid4()
    conflicting_header_id = uuid.uuid4()
    req = rf.get("/x", HTTP_X_SCHOOL_ID=str(conflicting_header_id))
    req.crown_tenant = SimpleNamespace(school_id=authorized_school_id)

    event = audit_log(request=req, action="tenant.authorized")

    assert event.school_id == authorized_school_id


def test_audit_log_supports_compatibility_tenant_school_id_without_header():
    rf = RequestFactory()
    school_id = uuid.uuid4()
    req = rf.get("/x")
    req.tenant_school_id = school_id

    event = audit_log(request=req, action="tenant.compatibility")

    assert event.school_id == school_id


def test_audit_log_falls_back_to_header_for_unbound_legacy_request():
    rf = RequestFactory()
    school_id = uuid.uuid4()
    req = rf.get("/x", HTTP_X_SCHOOL_ID=str(school_id))

    event = audit_log(request=req, action="tenant.legacy")

    assert event.school_id == school_id
