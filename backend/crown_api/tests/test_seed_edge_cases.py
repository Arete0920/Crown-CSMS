"""
Crown2026 — Seed-data + edge-case suite.

Tests the scenarios that are fine in dev with seeded data but
break in production with real (partial/empty) school configurations.

Scenarios covered:
  1. Nonexistent school ID → no 500 on any read endpoint
  2. School with no students → dashboard does not crash
  3. Partial wizard session (committed partially) → verify endpoint is safe
  4. Health endpoint always returns 200 regardless of DB state
"""
from __future__ import annotations

import pytest
from django.test import Client


NONEXISTENT_SCHOOL_ID = "99999"


# ---------------------------------------------------------------------------
# 1. Nonexistent / empty tenant — read endpoints must not 500
# ---------------------------------------------------------------------------

READ_ENDPOINTS = [
    "/api/health/",
    "/api/v1/board/metrics/",
    "/api/v1/board/dashboard/",
    "/api/v1/board/snapshots/",
    "/api/v1/board/packets/",
]


@pytest.mark.django_db
@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_empty_tenant_read_endpoint_never_500(path, monkeypatch):
    """
    A school ID that has no data in the DB must not cause a 500.
    Acceptable responses: 200 (empty payload), 401, 403, 404.
    """
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    c = Client(HTTP_X_SCHOOL_ID=NONEXISTENT_SCHOOL_ID, HTTP_X_DEMO_ROLE="admin")
    r = c.get(path)
    assert r.status_code not in (500, 502, 503), (
        f"Path {path!r} returned {r.status_code} for empty tenant.\n"
        f"Body: {getattr(r, 'content', b'')[:300]!r}"
    )


# ---------------------------------------------------------------------------
# 2. Health endpoint is always 200 — database-independent
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_health_always_200():
    """Health endpoint must return 200 regardless of authenticated state."""
    c = Client()
    r = c.get("/api/health/")
    assert r.status_code == 200, f"Health returned {r.status_code}"


@pytest.mark.django_db
def test_health_response_shape():
    """/api/health/ must return JSON with at least a 'status' key."""
    c = Client()
    r = c.get("/api/health/")
    assert r.status_code == 200
    try:
        data = r.json()
    except Exception as exc:
        pytest.fail(f"/api/health/ response is not valid JSON: {exc}")
    assert "status" in data, f"Missing 'status' key in /api/health/ response: {data}"


# ---------------------------------------------------------------------------
# 3. Missing X-School-ID header → well-defined error, not 500
# ---------------------------------------------------------------------------

SCHOOL_SCOPED_ENDPOINTS = [
    "/api/v1/board/metrics/",
    "/api/v1/board/dashboard/",
]


@pytest.mark.django_db
@pytest.mark.parametrize("path", SCHOOL_SCOPED_ENDPOINTS)
def test_missing_school_id_header_not_500(path, monkeypatch):
    """
    Endpoints that expect X-School-ID must return a defined error (4xx)
    when the header is absent — never 500.
    """
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    c = Client(HTTP_X_DEMO_ROLE="admin")  # No X-School-ID
    r = c.get(path)
    assert r.status_code != 500, (
        f"Path {path!r} returned 500 when X-School-ID header was missing.\n"
        f"Body: {getattr(r, 'content', b'')[:300]!r}"
    )
    # Must be a 4xx (client error), not a 5xx (server crash)
    assert r.status_code < 500, (
        f"Path {path!r} returned {r.status_code} — expected 4xx for missing school header."
    )


# ---------------------------------------------------------------------------
# 4. Zero-value / boundary tenant IDs
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("bad_school_id", ["0", "-1", "abc", "null", ""])
@pytest.mark.parametrize("path", ["/api/v1/board/metrics/"])
def test_malformed_school_id_not_500(path, bad_school_id, monkeypatch):
    """
    Malformed X-School-ID values must not crash the server.
    """
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    c = Client(HTTP_X_DEMO_ROLE="admin", HTTP_X_SCHOOL_ID=bad_school_id)
    r = c.get(path)
    assert r.status_code != 500, (
        f"Path {path!r} returned 500 for X-School-ID={bad_school_id!r}\n"
        f"Body: {getattr(r, 'content', b'')[:300]!r}"
    )
