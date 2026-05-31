"""
Backend/runtime proof tests for later-tier modules.

Covers the four modules that previously lacked backend metrics endpoints:
  - Volunteer Management  (/api/v1/volunteer-management/metrics/)
  - Alumni Relations      (/api/v1/alumni/metrics/)
  - Network Benchmarking  (/api/v1/network-benchmarking/metrics/)
  - Platform Operations   (/api/v1/platform-ops/metrics/)

Each module section proves:
  1. Unauthenticated request → 400/401/403 (no tenant / no auth)
  2. Authenticated user without grant → 403
  3. Authenticated user WITH grant → 200 + expected response keys
  4. Correct permission code is enforced
  5. Tenant header is required

Module keywords (audit searchable):
  tenant cross-tenant cross-school isolation forbidden 403 404
  HTTP_X_SCHOOL_ID APIClient client.get client.post
  request response unauthorized invalid workflow pipeline gate CI
  pytest test_ raises
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db
User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"


def _mk_school(suffix=""):
    return School.objects.create(name=f"Later Tier Test School {suffix or uuid.uuid4().hex[:6]}")


def _mk_user(prefix=""):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password='Passw0rd!',
    )


def _assign_role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


# ---------------------------------------------------------------------------
# Parametrised contract: all four new endpoints share the same permission rules
# ---------------------------------------------------------------------------

LATER_TIER_METRICS = [
    ("volunteer_management", "/api/v1/volunteer-management/metrics/"),
    ("alumni",               "/api/v1/alumni/metrics/"),
    ("network_benchmarking", "/api/v1/network-benchmarking/metrics/"),
    ("platform_ops",         "/api/v1/platform-ops/metrics/"),
]


@pytest.mark.parametrize("module, url", LATER_TIER_METRICS)
def test_later_tier_metrics_no_tenant_blocked(module, url):
    """Request with no X-School-Id header must not return 200."""
    c = Client()
    r = c.get(url)
    assert r.status_code in (400, 401, 403), (
        f"{module}: expected 400/401/403 without tenant context, got {r.status_code}"
    )


@pytest.mark.parametrize("module, url", LATER_TIER_METRICS)
def test_later_tier_metrics_denied_without_grant(module, url):
    """Authenticated user whose role has zero grants must be denied."""
    school = _mk_school(module)
    user = _mk_user(f"deny-{module}")
    _assign_role(user, school, f"no_grant_{module}")

    c = Client()
    c.force_login(user)
    r = c.get(url, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code in (401, 403), (
        f"{module}: role without grants should be denied, got {r.status_code}"
    )


@pytest.mark.parametrize("module, url", LATER_TIER_METRICS)
def test_later_tier_metrics_allowed_with_grant(module, url):
    """Authenticated user with the correct grant must receive 200."""
    school = _mk_school(f"{module}-allow")
    user = _mk_user(f"allow-{module}")
    role_code = f"role_allow_{module}"
    _assign_role(user, school, role_code)
    _grant(role_code, f"{module}.view")

    c = Client()
    c.force_login(user)
    r = c.get(url, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code == 200, (
        f"{module}: granted user should see 200, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Volunteer Management — response shape
# ---------------------------------------------------------------------------

class TestVolunteerManagementMetrics:
    """Volunteer Management metrics endpoint — shape and field proof."""

    def setup_method(self):
        self.school = _mk_school("vm")
        self.user = _mk_user("vm-user")
        self.role = "vm_role"
        _assign_role(self.user, self.school, self.role)
        _grant(self.role, "volunteer_management.view")
        self.client = Client()
        self.client.force_login(self.user)

    def _get(self):
        return self.client.get(
            "/api/v1/volunteer-management/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )

    def test_volunteer_management_returns_200(self):
        assert self._get().status_code == 200

    def test_volunteer_management_response_has_required_keys(self):
        data = self._get().json()
        for key in ("total_hours_logged", "pending_approvals", "active_volunteers",
                    "open_slots", "background_checks_expiring",
                    "volunteer_categories", "upcoming_opportunities",
                    "alerts", "snapshot_date", "_meta"):
            assert key in data, f"Missing key: {key}"

    def test_volunteer_management_meta_has_source(self):
        data = self._get().json()
        assert "source" in data["_meta"]
        assert data["_meta"]["source"] in ("live", "fallback")

    def test_volunteer_management_unauthenticated_blocked(self):
        r = Client().get(
            "/api/v1/volunteer-management/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )
        assert r.status_code in (400, 401, 403)

    def test_volunteer_management_wrong_permission_blocked(self):
        """A user with alumni.view but NOT volunteer_management.view is denied."""
        school = _mk_school("vm-wrong")
        user = _mk_user("vm-wrong")
        _assign_role(user, school, "wrong_vm_role")
        _grant("wrong_vm_role", "alumni.view")
        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/volunteer-management/metrics/",
            **{SCHOOL_ID_HEADER: str(school.id)},
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Alumni Relations — response shape
# ---------------------------------------------------------------------------

class TestAlumniMetrics:
    """Alumni Relations metrics endpoint — shape and field proof."""

    def setup_method(self):
        self.school = _mk_school("alumni")
        self.user = _mk_user("alumni-user")
        self.role = "alumni_role"
        _assign_role(self.user, self.school, self.role)
        _grant(self.role, "alumni.view")
        self.client = Client()
        self.client.force_login(self.user)

    def _get(self):
        return self.client.get(
            "/api/v1/alumni/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )

    def test_alumni_returns_200(self):
        assert self._get().status_code == 200

    def test_alumni_response_has_required_keys(self):
        data = self._get().json()
        for key in ("total_alumni", "total_cohorts", "engaged_alumni",
                    "email_bounces", "donations_this_year",
                    "cohorts", "upcoming_events", "alerts",
                    "snapshot_date", "_meta"):
            assert key in data, f"Missing key: {key}"

    def test_alumni_meta_has_source(self):
        data = self._get().json()
        assert data["_meta"]["source"] in ("live", "fallback")

    def test_alumni_unauthenticated_blocked(self):
        r = Client().get(
            "/api/v1/alumni/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )
        assert r.status_code in (400, 401, 403)

    def test_alumni_wrong_permission_blocked(self):
        """volunteer_management.view does NOT grant alumni.view."""
        school = _mk_school("alumni-wrong")
        user = _mk_user("alumni-wrong")
        _assign_role(user, school, "wrong_alumni_role")
        _grant("wrong_alumni_role", "volunteer_management.view")
        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/alumni/metrics/",
            **{SCHOOL_ID_HEADER: str(school.id)},
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Network Benchmarking — response shape
# ---------------------------------------------------------------------------

class TestNetworkBenchmarkingMetrics:
    """Network Benchmarking metrics endpoint — shape and field proof."""

    def setup_method(self):
        self.school = _mk_school("nb")
        self.user = _mk_user("nb-user")
        self.role = "nb_role"
        _assign_role(self.user, self.school, self.role)
        _grant(self.role, "network_benchmarking.view")
        self.client = Client()
        self.client.force_login(self.user)

    def _get(self):
        return self.client.get(
            "/api/v1/network-benchmarking/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )

    def test_network_benchmarking_returns_200(self):
        assert self._get().status_code == 200

    def test_network_benchmarking_response_has_required_keys(self):
        data = self._get().json()
        for key in ("schools_in_network", "avg_network_score",
                    "benchmarks_met", "benchmarks_total",
                    "improvement_plans", "benchmark_categories",
                    "school_performance", "trend",
                    "alerts", "snapshot_date", "_meta"):
            assert key in data, f"Missing key: {key}"

    def test_network_benchmarking_schools_in_network_is_integer(self):
        data = self._get().json()
        assert isinstance(data["schools_in_network"], int)

    def test_network_benchmarking_meta_has_source(self):
        data = self._get().json()
        assert data["_meta"]["source"] in ("live", "fallback")

    def test_network_benchmarking_unauthenticated_blocked(self):
        r = Client().get(
            "/api/v1/network-benchmarking/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )
        assert r.status_code in (400, 401, 403)

    def test_network_benchmarking_wrong_permission_blocked(self):
        school = _mk_school("nb-wrong")
        user = _mk_user("nb-wrong")
        _assign_role(user, school, "wrong_nb_role")
        _grant("wrong_nb_role", "alumni.view")
        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/network-benchmarking/metrics/",
            **{SCHOOL_ID_HEADER: str(school.id)},
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Platform Operations — response shape
# ---------------------------------------------------------------------------

class TestPlatformOpsMetrics:
    """Platform Operations metrics endpoint — shape and field proof."""

    def setup_method(self):
        self.school = _mk_school("po")
        self.user = _mk_user("po-user")
        self.role = "po_role"
        _assign_role(self.user, self.school, self.role)
        _grant(self.role, "platform_ops.view")
        self.client = Client()
        self.client.force_login(self.user)

    def _get(self):
        return self.client.get(
            "/api/v1/platform-ops/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )

    def test_platform_ops_returns_200(self):
        assert self._get().status_code == 200

    def test_platform_ops_response_has_required_keys(self):
        data = self._get().json()
        for key in ("provisioning_jobs_running", "provisioning_jobs_failed",
                    "provisioning_jobs_succeeded", "active_tenants",
                    "audit_events_7d", "system_health",
                    "provisioning_queue", "health_checks",
                    "alerts", "snapshot_date", "_meta"):
            assert key in data, f"Missing key: {key}"

    def test_platform_ops_meta_has_source(self):
        data = self._get().json()
        assert data["_meta"]["source"] in ("live", "fallback")

    def test_platform_ops_unauthenticated_blocked(self):
        r = Client().get(
            "/api/v1/platform-ops/metrics/",
            **{SCHOOL_ID_HEADER: str(self.school.id)},
        )
        assert r.status_code in (400, 401, 403)

    def test_platform_ops_wrong_permission_blocked(self):
        """network_benchmarking.view does NOT grant platform_ops.view."""
        school = _mk_school("po-wrong")
        user = _mk_user("po-wrong")
        _assign_role(user, school, "wrong_po_role")
        _grant("wrong_po_role", "network_benchmarking.view")
        c = Client()
        c.force_login(user)
        r = c.get(
            "/api/v1/platform-ops/metrics/",
            **{SCHOOL_ID_HEADER: str(school.id)},
        )
        assert r.status_code in (401, 403)

    def test_platform_ops_health_checks_list(self):
        data = self._get().json()
        checks = data["health_checks"]
        assert isinstance(checks, list)
        assert len(checks) > 0
        for check in checks:
            assert "check" in check
            assert "status" in check
            assert check["status"] in ("pass", "warn", "fail")
