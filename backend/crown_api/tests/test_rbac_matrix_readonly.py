"""
Crown2026 — RBAC matrix: read-only endpoint no-500 guarantee.

Phase 1 (current): guarantees NO endpoint returns HTTP 500 for any role.
Phase 2 (future): replace the `assert != 500` with an expected_status matrix
  from a JSON fixture to enforce correct 200/403 per role.

Fixture file: fixtures/rbac_endpoints_readonly.txt
  - One URL path per line (absolute, e.g. /api/health/)
  - Lines starting with # are ignored

Roles tested: the set of demo role header values your stack accepts.
  Adjust ROLES if your role names differ.
"""
from __future__ import annotations

import pathlib

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
