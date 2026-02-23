# backend/financial_aid/tests/test_financial_aid_authz.py
#
# Layer C — Permission gate contract tests for /api/v1/financial-aid/*.
#
# Verifies that roles WITHOUT financial_aid.view are hard-blocked (403),
# and that roles WITH it reach the data layer (200).
#
# Tenant isolation (row scope) is also proven here:
# a user with financial_aid.view in School A cannot read School B's data.
#
# Suite contract:
#   - No test relies on suite ordering.
#   - Uses pytest-django fixtures (not APITestCase) for consistency with nav tests.

import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from financial_aid.models import AidAward, AidBucket, FinancialAidApplication

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _enable_tenant_middleware(settings):
    """Force TENANT_HEADER_REQUIRED=True for all FA authz tests.
    The root conftest.py disables it globally; permission gate and cross-tenant
    tests require the middleware to set request.school correctly.
    """
    settings.TENANT_HEADER_REQUIRED = True


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

def _school(name="FA Authz School"):
    return School.objects.create(name=f"{name}-{uuid.uuid4()}")


def _user(label="u"):
    return UserAccount.objects.create_user(
        username=f"{label}-{uuid.uuid4()}",
        password="Passw0rd!",
    )


def _assign_role(user, school, role_code):
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(
        code=perm_code, defaults={"description": ""}
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def _seed_fa_data(school_id):
    """Create one application + one award for a school, returns (app, award)."""
    hh_id = uuid.uuid4()
    app = FinancialAidApplication.objects.create(
        school_id=school_id,
        household_id=hh_id,
        academic_year="2026-2027",
        household_income="55000.00",
        household_size=4,
        status="decided",
    )
    award = AidAward.objects.create(
        school_id=school_id,
        application=app,
        bucket=AidBucket.NEED,
        amount="8000.00",
        rationale="Demonstrable need",
    )
    return app, award


# ──────────────────────────────────────────────────────────────────────────────
# 403 gate: roles that must never reach financial aid data
# ──────────────────────────────────────────────────────────────────────────────

class TestFinancialAidPermissionGate:
    """Roles without financial_aid.view must get 403 on both endpoints."""

    @pytest.mark.parametrize("role_code,perm_code", [
        ("PARENT",  "parent.view"),
        ("STUDENT", "student.view"),
        ("TEACHER", "teacher.view"),
    ])
    def test_role_blocked_on_summary(self, role_code, perm_code):
        school = _school("Gate Test")
        user = _user(role_code.lower())
        _assign_role(user, school, role_code)
        _grant(role_code, perm_code)

        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert r.status_code == 403, (
            f"Role {role_code!r} should be blocked from financial-aid/summary/ "
            f"but got {r.status_code}"
        )

    @pytest.mark.parametrize("role_code,perm_code", [
        ("PARENT",  "parent.view"),
        ("STUDENT", "student.view"),
        ("TEACHER", "teacher.view"),
    ])
    def test_role_blocked_on_drilldown(self, role_code, perm_code):
        school = _school("Gate Test DD")
        user = _user(f"{role_code.lower()}_dd")
        _assign_role(user, school, role_code)
        _grant(role_code, perm_code)

        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/financial-aid/drilldown/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert r.status_code == 403, (
            f"Role {role_code!r} should be blocked from financial-aid/drilldown/ "
            f"but got {r.status_code}"
        )

    def test_unauthenticated_gets_403_not_data(self):
        """Anonymous requests must not reach FA data layer."""
        school = _school("Anon Gate")
        c = Client()
        r = c.get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        # DRF IsAuthenticated returns 403 for anonymous by default
        assert r.status_code in (401, 403)


# ──────────────────────────────────────────────────────────────────────────────
# 200 gate: roles that must reach financial aid data
# ──────────────────────────────────────────────────────────────────────────────

class TestFinancialAidPermissionAllowed:
    """Roles WITH financial_aid.view must reach data (200)."""

    @pytest.mark.parametrize("role_code", ["AID_DIRECTOR", "FINANCE_DIRECTOR"])
    def test_role_reaches_summary(self, role_code):
        school = _school("Allowed Test")
        user = _user(role_code.lower())
        _assign_role(user, school, role_code)
        _grant(role_code, "financial_aid.view")

        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert r.status_code == 200, (
            f"Role {role_code!r} should reach financial-aid/summary/ "
            f"but got {r.status_code}"
        )

    @pytest.mark.parametrize("role_code", ["AID_DIRECTOR", "FINANCE_DIRECTOR"])
    def test_role_reaches_drilldown(self, role_code):
        school = _school("Allowed DD Test")
        user = _user(f"{role_code.lower()}_dd2")
        _assign_role(user, school, role_code)
        _grant(role_code, "financial_aid.view")
        _seed_fa_data(school.id)

        c = Client()
        c.force_login(user)
        r = c.get(
            f"/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert r.status_code == 200, (
            f"Role {role_code!r} should reach financial-aid/drilldown/ "
            f"but got {r.status_code}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Tenant isolation (row scope)
# ──────────────────────────────────────────────────────────────────────────────

class TestFinancialAidTenantIsolation:
    """User in School A must not see School B's financial aid data."""

    def test_cross_tenant_row_isolation_on_drilldown(self):
        school_a = _school("FA Tenant A")
        school_b = _school("FA Tenant B")

        # Aid director for school_a only
        user = _user("aiddir_isolation")
        _assign_role(user, school_a, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.view")

        # Seed data in school_b only — user should not see it
        _seed_fa_data(school_b.id)

        c = Client()
        c.force_login(user)

        # Request against school_b while user only has a role in school_a.
        # Middleware will resolve school_b from the header, so request.school = school_b.
        # user_has_permission(user, "financial_aid.view", school=school_b) → False
        # (user has AID_DIRECTOR role in school_a, not school_b)
        r = c.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school_b.id),
        )
        assert r.status_code == 403, (
            f"User with role in school_a should be blocked from school_b FA data, "
            f"got {r.status_code}"
        )

    def test_same_tenant_drilldown_returns_own_data_only(self):
        school_a = _school("FA Own Data A")
        school_b = _school("FA Own Data B")

        user = _user("aiddir_own")
        _assign_role(user, school_a, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.view")

        # Data in school_a (user's school) and school_b (foreign)
        _seed_fa_data(school_a.id)
        _seed_fa_data(school_b.id)

        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school_a.id),
        )
        assert r.status_code == 200
        data = r.json()
        # All returned rows must belong to school_a
        for row in data.get("rows", []):
            # The drilldown filters by school_id from require_school_id(request)
            # which reads the header — so rows are always scoped to the requested school
            assert row.get("award_id") is not None  # sanity: rows have IDs
        # total should reflect only school_a's records (1 award seeded)
        assert data["total"] == 1, (
            f"Expected 1 award for school_a, got {data['total']} "
            f"(school_b data must not leak)"
        )
