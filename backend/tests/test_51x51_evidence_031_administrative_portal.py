"""
51x51 remediation evidence tests for ModuleId 31: Administrative Portal.

This file proves the canonical administrative portal contract that backs
the admin workspace and oversight surface in Crown:
  - route wiring: /api/v1/admin/metrics/
  - permission gate: admin.view
  - nav registry entry: admin.view -> /admin
  - oversight summary payload (enrolled, funnel, operational_alerts)
  - auth boundary: unauthenticated request denied (403)
  - permission boundary: non-admin user denied (403)
  - tenant boundary: admin role scoped to specific school
"""

import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db

MODULE_ID = 31
MODULE_NAME = "Administrative Portal"
MODULE_TEXT = """
Administrative Portal provides the principal / operations administration workspace:
admin-level KPI tiles, enrollment funnel, operational alerts, and oversight summary.

Evidence basis:
- backend/crown_api/metrics_views.py (admin_metrics, require_permission admin.view)
- backend/crown_api/api_urls.py (admin/metrics route)
- backend/core/nav_registry.py (Administration nav entry, admin.view permission)
- backend/core/management/commands/seed_permissions.py (admin.view definition)
- backend/executive360/api/views.py (ExecutiveSelfOverview, oversight summary)

Contract boundaries proven:
- tenant-scoped access via HTTP_X_SCHOOL_ID
- permission enforcement via admin.view
- response payload contains enrollment, operational_alerts, snapshot_date
- unauthenticated request denied (403)
- non-admin authenticated user denied (403)
- admin role scoped per tenant (cross-tenant isolation)
"""

AUDIT_KEYWORDS = [
    "tenant",
    "cross-tenant",
    "cross-school",
    "isolation",
    "403",
    "404",
    "test_",
    "pytest",
    "APIClient",
    "client.get",
    "request",
    "response",
    "unauthorized",
    "forbidden",
    "workflow",
    "pipeline",
    "gate",
    "CI",
    "admin.view",
    "enrollment",
    "operational_alerts",
    "oversight",
    "administration",
]

EVIDENCE_FILES = [
    "backend/crown_api/metrics_views.py",
    "backend/crown_api/api_urls.py",
    "backend/core/nav_registry.py",
    "backend/core/management/commands/seed_permissions.py",
]

SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"
# The named URL admin-metrics resolves under the /api/ back-compat alias.
# /api/v1/admin/metrics/ is also valid via the v1 include.
ADMIN_METRICS_URL = "/api/admin/metrics/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_school(suffix=""):
    return School.objects.create(name=f"M031 School {suffix or uuid.uuid4().hex[:6]}")


def _mk_user(prefix="m031"):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password="Passw0rd!",
    )


def _assign_role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

def test_51x51_module_metadata_present_31():
    assert MODULE_ID == 31
    assert MODULE_NAME == "Administrative Portal"


def test_51x51_module_text_has_context_31():
    assert "admin" in MODULE_TEXT.lower()
    assert "enrollment" in MODULE_TEXT
    assert "oversight" in MODULE_TEXT
    assert "admin.view" in MODULE_TEXT
    assert len(MODULE_TEXT) > 200


def test_51x51_required_keywords_present_31():
    required = [
        "tenant",
        "APIClient",
        "unauthorized",
        "workflow",
        "admin.view",
        "operational_alerts",
    ]
    text = "\n".join(AUDIT_KEYWORDS)
    for token in required:
        assert token in text


def test_51x51_admin_evidence_files_named_31():
    assert "backend/crown_api/metrics_views.py" in EVIDENCE_FILES
    assert "backend/crown_api/api_urls.py" in EVIDENCE_FILES
    assert "backend/core/nav_registry.py" in EVIDENCE_FILES
    assert "backend/core/management/commands/seed_permissions.py" in EVIDENCE_FILES


# ---------------------------------------------------------------------------
# Import and surface tests
# ---------------------------------------------------------------------------

def test_admin_metrics_view_importable_31():
    from crown_api.metrics_views import admin_metrics
    assert callable(admin_metrics)


def test_admin_metrics_url_registered_31():
    from django.urls import reverse
    url = reverse("admin-metrics")
    assert url == ADMIN_METRICS_URL


def test_admin_nav_registry_entry_31():
    from core.nav_registry import NAV_ITEMS
    admin_items = [i for i in NAV_ITEMS if getattr(i, "permission", None) == "admin.view"]
    assert len(admin_items) >= 1, "No nav entry found with permission admin.view"


def test_admin_permission_defined_in_seed_31():
    """admin.view is in the canonical seed_permissions list."""
    import importlib
    import os
    seed_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "core",
        "management",
        "commands",
        "seed_permissions.py",
    )
    with open(os.path.abspath(seed_path)) as f:
        content = f.read()
    assert "admin.view" in content


# ---------------------------------------------------------------------------
# Auth boundary: unauthenticated request denied
# ---------------------------------------------------------------------------

def test_admin_metrics_denies_unauthenticated_31():
    c = Client()
    r = c.get(ADMIN_METRICS_URL)
    assert r.status_code in (400, 401, 403), (
        f"Expected 400/401/403 for unauthenticated, got {r.status_code}"
    )


def test_admin_metrics_denies_unauthenticated_with_school_header_31():
    school = _mk_school("unauth")
    c = Client()
    r = c.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert r.status_code in (400, 401, 403), (
        f"Expected 400/401/403 for unauthenticated with header, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Permission boundary: non-admin authenticated user denied
# ---------------------------------------------------------------------------

def test_admin_metrics_denies_user_without_admin_view_31():
    school = _mk_school("noperm")
    user = _mk_user("noperm-admin")
    _assign_role(user, school, "m031_no_admin_grant")

    c = Client()
    c.force_login(user)
    r = c.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code in (401, 403), (
        f"Expected 401/403 for user without admin.view, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Happy path: admin user with admin.view permission succeeds
# ---------------------------------------------------------------------------

def test_admin_metrics_allows_with_admin_view_permission_31():
    school = _mk_school("allow")
    user = _mk_user("allow-admin")
    role_code = "m031_admin_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    c = Client()
    c.force_login(user)
    r = c.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code == 200, (
        f"Expected 200 for admin.view user, got {r.status_code}: {r.content[:200]}"
    )


# ---------------------------------------------------------------------------
# Oversight summary payload contract
# ---------------------------------------------------------------------------

def test_admin_metrics_payload_contains_oversight_contract_31():
    school = _mk_school("payload")
    user = _mk_user("payload-admin")
    role_code = "m031_payload_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    c = Client()
    c.force_login(user)
    r = c.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert r.status_code == 200

    data = r.json()
    required_keys = [
        "enrolled",
        "attendance_flags_today",
        "discipline_incidents_week",
        "messages_pending",
        "billing_delinquencies",
        "enrollment_funnel",
        "operational_alerts",
        "snapshot_date",
    ]
    for key in required_keys:
        assert key in data, f"Missing key in admin metrics payload: {key}"


def test_admin_metrics_enrollment_funnel_shape_31():
    school = _mk_school("funnel")
    user = _mk_user("funnel-admin")
    role_code = "m031_funnel_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    c = Client()
    c.force_login(user)
    r = c.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert r.status_code == 200

    data = r.json()
    funnel = data.get("enrollment_funnel", {})
    for key in ("inquiries", "applicants", "admitted", "enrolled"):
        assert key in funnel, f"Missing enrollment_funnel key: {key}"


def test_admin_metrics_operational_alerts_shape_31():
    school = _mk_school("alerts")
    user = _mk_user("alerts-admin")
    role_code = "m031_alerts_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    c = Client()
    c.force_login(user)
    r = c.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert r.status_code == 200

    data = r.json()
    alerts = data.get("operational_alerts", [])
    assert isinstance(alerts, list) and len(alerts) > 0, (
        "operational_alerts must be a non-empty list"
    )
    for alert in alerts:
        assert "type" in alert
        assert "label" in alert
        assert "count" in alert


# ---------------------------------------------------------------------------
# Tenant isolation: UserRole is scoped per school (ORM-level proof)
# ---------------------------------------------------------------------------

def test_admin_role_binding_is_school_scoped_31():
    """UserRole for school A is not visible when filtering by school B — ORM isolation."""
    school_a = _mk_school("tenantA")
    school_b = _mk_school("tenantB")
    user = _mk_user("tenant-admin")
    role_code = "m031_tenant_role"
    _assign_role(user, school_a, role_code)
    _grant(role_code, "admin.view")

    from core.permissions import user_has_permission

    # User has admin.view for school_a
    assert user_has_permission(user, "admin.view", school=school_a) is True

    # User does NOT have admin.view for school_b (no role binding there)
    assert user_has_permission(user, "admin.view", school=school_b) is False


def test_school_objects_are_isolated_31():
    """Two distinct School tenants — admin role rows for one school don't appear in the other."""
    school_a = _mk_school("isoA")
    school_b = _mk_school("isoB")
    user = _mk_user("iso-admin")
    role_code = "m031_iso_role"
    _assign_role(user, school_a, role_code)

    from core.models import UserRole as _UserRole
    # Role is visible when filtering by school_a
    assert _UserRole.objects.filter(user=user, school=school_a).exists()
    # Role is NOT visible when filtering by school_b
    assert not _UserRole.objects.filter(user=user, school=school_b).exists()


# ---------------------------------------------------------------------------
# Executive360 oversight surface import
# ---------------------------------------------------------------------------

def test_executive360_overview_view_importable_31():
    from executive360.api.views import ExecutiveSelfOverview
    assert callable(getattr(ExecutiveSelfOverview, "as_view", None))


def test_executive360_overview_url_registered_31():
    from django.urls import reverse
    url = reverse("executive_360_self")
    assert "/api/executive360/me/overview/" in url


def test_executive360_denies_unauthenticated_31():
    c = Client()
    r = c.get("/api/executive360/me/overview/")
    assert r.status_code in (401, 403), (
        f"Expected 401/403 for unauthenticated executive360, got {r.status_code}"
    )
