"""
Crown2026 — RBAC matrix: read-only endpoint correctness.

Phase 1 (current): guarantees NO endpoint returns HTTP 500 for any role.
Phase 2 (current): explicit status expectations per endpoint category:
  - PUBLIC endpoints: must return 200 for any caller (authenticated or not)
  - PROTECTED endpoints: must return 401 or 403 for unauthenticated callers
  - PROTECTED endpoints with demo-role auth: must return non-500

Fixture file: fixtures/rbac_endpoints_readonly.txt
  - One URL path per line (absolute, e.g. /api/health/)
  - Lines starting with # are ignored

Roles tested: the set of demo role header values your stack accepts.
  Adjust ROLES if your role names differ.
"""
from __future__ import annotations

import pathlib
from typing import Any

import pytest
from django.test import Client

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "rbac_endpoints_readonly.txt"

# Demo role header values exercised.
# Must match what ALLOW_DEMO_ROLE_HEADER=1 mode accepts in your RBAC middleware.
ROLES = [
    "admin",
    "SCHOOL_ADMIN",
    "BOARD_MEMBER",
    "FINANCE",
    "ADMISSIONS",
    "TEACHER",
    "PARENT",
]


def _load_endpoints() -> list[str]:
    if not FIXTURE.exists():
        raise FileNotFoundError(f"RBAC fixture not found: {FIXTURE}")
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def pytest_generate_tests(metafunc):
    """Dynamic parametrization so the fixture file is the source of truth."""
    if "rbac_path" in metafunc.fixturenames:
        metafunc.parametrize("rbac_path", _load_endpoints(), ids=lambda p: p.replace("/", "_"))
    if "rbac_role" in metafunc.fixturenames:
        metafunc.parametrize("rbac_role", ROLES)


@pytest.mark.django_db
def test_readonly_endpoint_never_500(rbac_path, rbac_role, monkeypatch):
    """
    No read-only endpoint may return HTTP 500 for any role.
    500 = unhandled exception in production code. Always a bug.
    """
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    c = Client(HTTP_X_DEMO_ROLE=rbac_role, HTTP_X_SCHOOL_ID="1")
    r = c.get(rbac_path)
    assert r.status_code != 500, (
        f"HTTP 500 on GET {rbac_path!r} with role={rbac_role!r}\n"
        f"Response body (first 500 chars): {getattr(r, 'content', b'')[:500]!r}"
    )


@pytest.mark.django_db
def test_readonly_endpoint_unauthenticated_never_500(rbac_path):
    """
    Unauthenticated requests must also never produce 500.
    Expected: 401, 403, or 200 (for public endpoints like /api/health/).
    """
    c = Client(HTTP_X_SCHOOL_ID="1")
    r = c.get(rbac_path)
    assert r.status_code != 500, (
        f"HTTP 500 on unauthenticated GET {rbac_path!r}\n"
        f"Response body (first 500 chars): {getattr(r, 'content', b'')[:500]!r}"
    )


# ---------------------------------------------------------------------------
# Phase 2: Explicit status expectations by endpoint category
# ---------------------------------------------------------------------------

# Endpoints that MUST return 200 regardless of auth state.
# These are infrastructure/health endpoints that no gating should block.
PUBLIC_MUST_200: list[str] = [
    "/api/health/",
]

# Endpoints that MUST require auth — unauthenticated callers must get 401 or 403.
# This is the "no authenticated-bypass" check: these routes are NOT public.
AUTH_REQUIRED_ENDPOINTS: list[str] = [
    "/api/v1/board/metrics/",
    "/api/v1/board/dashboard/",
    "/api/v1/board/snapshots/",
    "/api/v1/board/packets/",
    "/api/v1/financial-aid/summary/",
]


@pytest.mark.django_db
@pytest.mark.parametrize("path", PUBLIC_MUST_200)
def test_public_endpoint_always_200(path):
    """
    Public endpoints (health, readiness, etc.) must return 200
    for any caller — authenticated or not. These MUST NOT require auth.
    """
    c = Client()
    r = c.get(path)
    assert r.status_code == 200, (
        f"Public endpoint {path!r} returned {r.status_code} — expected 200.\n"
        f"These endpoints must be ungated (never require auth).\n"
        f"Body: {getattr(r, 'content', b'')[:300]!r}"
    )


@pytest.mark.django_db
def test_health_returns_build_sha_key():
    """
    /api/health/ must include a 'build_sha' key in the JSON response.
    This is the runtime deployment integrity proof.
    """
    c = Client()
    r = c.get("/api/health/")
    assert r.status_code == 200
    try:
        data = r.json()
    except Exception as exc:
        pytest.fail(f"/api/health/ response is not valid JSON: {exc}")
    assert "build_sha" in data, (
        f"'build_sha' missing from /api/health/ response. Got keys: {list(data.keys())}"
    )
    assert "status" in data, (
        f"'status' missing from /api/health/ response. Got keys: {list(data.keys())}"
    )
    # build_sha must not be empty
    assert data["build_sha"], (
        f"'build_sha' in /api/health/ is empty or falsy: {data['build_sha']!r}"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("path", AUTH_REQUIRED_ENDPOINTS)
def test_protected_endpoint_requires_auth(path):
    """
    Protected endpoints must return 401 or 403 for unauthenticated callers.
    A 200 here means the endpoint is inadvertently public — an auth bypass.
    """
    c = Client(HTTP_X_SCHOOL_ID="1")
    r = c.get(path)
    assert r.status_code in (400, 401, 403), (
        f"Protected endpoint {path!r} returned {r.status_code} for unauthenticated request.\n"
        f"Expected 401 or 403 (auth required).\n"
        f"If 200: auth bypass detected — this is a security regression.\n"
        f"Body: {getattr(r, 'content', b'')[:300]!r}"
    )
    # Explicit 200/500 failing assertions for clarity in CI output
    assert r.status_code != 200, (
        f"AUTH BYPASS: {path!r} returned 200 without authentication."
    )
    assert r.status_code != 500, (
        f"SERVER ERROR: {path!r} returned 500 on unauthenticated request."
    )
