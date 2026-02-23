# backend/crown_api/tests/test_metrics_permissions_contract.py
#
# Contract tests: every /api/v1/*/metrics/ endpoint must enforce permissions.
#   - No tenant context        → 400 / 401 / 403
#   - Authenticated, no grant  → 401 / 403
#   - Authenticated + granted  → 200
#
# Scoped to the 27 endpoints that are currently registered in api_urls.py.

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, UserAccount, School, UserRole

pytestmark = pytest.mark.django_db

SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"


def mk_school():
    return School.objects.create(name="Demo School")


def mk_user(username):
    return UserAccount.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="pass12345",
    )


def assign_role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


# ──────────────────────────────────────────────────────────────────────────────
# All currently registered metrics endpoints.
# module code maps to <module>.view permission used by require_permission().
# ──────────────────────────────────────────────────────────────────────────────
METRICS = [
    ("admin",            "/api/v1/admin/metrics/"),
    ("board",            "/api/v1/board/metrics/"),
    ("finance",          "/api/v1/finance/metrics/"),
    ("teacher",          "/api/v1/teacher/metrics/"),
    ("parent",           "/api/v1/parent/metrics/"),
    ("student",          "/api/v1/student/metrics/"),
    ("it",               "/api/v1/it/metrics/"),
    ("financial_aid",    "/api/v1/financial-aid/metrics/"),
    ("marketing",        "/api/v1/marketing/metrics/"),
    ("spiritual_life",   "/api/v1/spiritual-life/metrics/"),
    ("office",           "/api/v1/office/metrics/"),
    ("health",           "/api/v1/health/metrics/"),
    ("counseling",       "/api/v1/counseling/metrics/"),
    ("food",             "/api/v1/food/metrics/"),
    ("athletics",        "/api/v1/athletics/metrics/"),
    ("advancement",      "/api/v1/advancement/metrics/"),
    ("transportation",   "/api/v1/transportation/metrics/"),
    ("facilities",       "/api/v1/facilities/metrics/"),
    ("security",         "/api/v1/security/metrics/"),
    ("academic_support", "/api/v1/academic-support/metrics/"),
    ("fine_arts",        "/api/v1/fine-arts/metrics/"),
    ("library",          "/api/v1/library/metrics/"),
    ("extended_care",    "/api/v1/extended-care/metrics/"),
    ("registrar",        "/api/v1/registrar/metrics/"),
    ("communications",   "/api/v1/communications/metrics/"),
    ("pd",               "/api/v1/pd/metrics/"),
    ("student_services", "/api/v1/student-services/metrics/"),
]


@pytest.mark.parametrize("module, url", METRICS)
def test_metrics_requires_tenant_context(module, url):
    """
    Requests with no X-School-Id header must never return 200.
    Middleware returns 400; auth-first paths return 401/403.
    """
    c = Client()
    r = c.get(url)
    assert r.status_code in (400, 401, 403), (
        f"{module}: expected 400/401/403 without tenant context, got {r.status_code}"
    )


@pytest.mark.parametrize("module, url", METRICS)
def test_metrics_denies_without_permission(module, url):
    """
    An authenticated user whose role has no grants for this module must be
    rejected with 401 or 403 — never 200.
    """
    school = mk_school()
    u = mk_user(f"deny_{module}")
    assign_role(u, school, "no_perm_role")  # role with zero grants

    c = Client()
    c.force_login(u)
    r = c.get(url, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code in (401, 403), (
        f"{module}: role without grants unexpectedly allowed — got {r.status_code}"
    )


@pytest.mark.parametrize("module, url", METRICS)
def test_metrics_allows_with_permission(module, url):
    """
    An authenticated user whose role IS granted <module>.view must receive 200.
    """
    school = mk_school()
    u = mk_user(f"allow_{module}")
    assign_role(u, school, "contract_tester")

    grant("contract_tester", f"{module}.view")

    c = Client()
    c.force_login(u)
    r = c.get(url, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code == 200, (
        f"{module}: granted user should see 200, got {r.status_code}"
    )
