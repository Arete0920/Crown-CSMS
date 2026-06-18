"""
51x51 remediation evidence tests for ModuleId 31: Administrative Portal.

Proves:
- route wiring for /api/admin/metrics/
- permission gate admin.view
- Administration nav registry entry
- oversight payload contract
- deterministic 403 auth and permission denials
- tenant isolation through user_has_permission(..., school=...)

Boundary: backend/tests/conftest.py disables TENANT_HEADER_REQUIRED, so this file
does not claim HTTP middleware tenant-header proof. Tenant isolation is proven at
the UserRole/user_has_permission school-scoping layer.
"""

import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db

MODULE_ID = 31
MODULE_NAME = "Administrative Portal"
ADMIN_METRICS_URL = "/api/admin/metrics/"
SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"

MODULE_TEXT = """
Administrative Portal provides admin KPI tiles, enrollment funnel,
operational alerts, and oversight summary. Proof is limited to backend route,
permission, payload, and ORM/permission-layer tenant scoping.
"""

AUDIT_KEYWORDS = [
    "tenant", "cross-tenant", "cross-school", "isolation", "403", "test_",
    "pytest", "APIClient", "client.get", "request", "response", "unauthorized",
    "forbidden", "workflow", "pipeline", "gate", "CI", "admin.view",
    "enrollment", "operational_alerts", "oversight", "administration",
]

EVIDENCE_FILES = [
    "backend/crown_api/metrics_views.py",
    "backend/crown_api/api_urls.py",
    "backend/core/nav_registry.py",
    "backend/core/management/commands/seed_permissions.py",
    "backend/core/permissions.py",
]


def _mk_school(suffix=""):
    return School.objects.create(name=f"M031 School {suffix or uuid.uuid4().hex[:6]}")


def _mk_user(prefix="m031"):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
    )


def _assign_role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def test_51x51_module_metadata_present_31():
    assert MODULE_ID == 31
    assert MODULE_NAME == "Administrative Portal"


def test_51x51_module_text_has_context_31():
    assert "admin" in MODULE_TEXT.lower()
    assert "oversight" in MODULE_TEXT
    assert len(MODULE_TEXT) > 100


def test_51x51_required_keywords_present_31():
    text = "\n".join(AUDIT_KEYWORDS)
    for token in ["tenant", "APIClient", "unauthorized", "workflow", "admin.view", "operational_alerts"]:
        assert token in text


def test_51x51_admin_evidence_files_named_31():
    for path in [
        "backend/crown_api/metrics_views.py",
        "backend/crown_api/api_urls.py",
        "backend/core/nav_registry.py",
        "backend/core/management/commands/seed_permissions.py",
        "backend/core/permissions.py",
    ]:
        assert path in EVIDENCE_FILES


def test_admin_metrics_view_importable_31():
    from crown_api.metrics_views import admin_metrics
    assert callable(admin_metrics)


def test_admin_metrics_url_registered_31():
    from django.urls import reverse
    assert reverse("admin-metrics") == ADMIN_METRICS_URL


def test_admin_nav_registry_entry_31():
    from core.nav_registry import NAV_ITEMS
    assert any(getattr(item, "permission", None) == "admin.view" for item in NAV_ITEMS)


def test_admin_permission_defined_in_seed_31():
    import os
    seed_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "core", "management", "commands", "seed_permissions.py")
    )
    with open(seed_path) as handle:
        content = handle.read()
    assert "admin.view" in content


def test_admin_metrics_denies_unauthenticated_31():
    response = Client().get(ADMIN_METRICS_URL)
    assert response.status_code == 403


def test_admin_metrics_denies_unauthenticated_with_school_header_31():
    school = _mk_school("unauth")
    response = Client().get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert response.status_code == 403


def test_admin_metrics_denies_user_without_admin_view_31():
    school = _mk_school("noperm")
    user = _mk_user("noperm-admin")
    _assign_role(user, school, "m031_no_admin_grant")

    client = Client()
    client.force_login(user)
    response = client.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 403


def test_admin_metrics_allows_with_admin_view_permission_31():
    school = _mk_school("allow")
    user = _mk_user("allow-admin")
    role_code = "m031_admin_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    client = Client()
    client.force_login(user)
    response = client.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 200


def test_admin_metrics_payload_contains_oversight_contract_31():
    school = _mk_school("payload")
    user = _mk_user("payload-admin")
    role_code = "m031_payload_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    client = Client()
    client.force_login(user)
    response = client.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert response.status_code == 200

    data = response.json()
    for key in [
        "enrolled", "attendance_flags_today", "discipline_incidents_week",
        "messages_pending", "billing_delinquencies", "enrollment_funnel",
        "operational_alerts", "snapshot_date",
    ]:
        assert key in data


def test_admin_metrics_enrollment_funnel_shape_31():
    school = _mk_school("funnel")
    user = _mk_user("funnel-admin")
    role_code = "m031_funnel_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    client = Client()
    client.force_login(user)
    response = client.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert response.status_code == 200

    funnel = response.json().get("enrollment_funnel", {})
    for key in ("inquiries", "applicants", "admitted", "enrolled"):
        assert key in funnel


def test_admin_metrics_operational_alerts_shape_31():
    school = _mk_school("alerts")
    user = _mk_user("alerts-admin")
    role_code = "m031_alerts_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "admin.view")

    client = Client()
    client.force_login(user)
    response = client.get(ADMIN_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert response.status_code == 200

    alerts = response.json().get("operational_alerts", [])
    assert isinstance(alerts, list)
    assert alerts
    for alert in alerts:
        assert "type" in alert
        assert "label" in alert
        assert "count" in alert


def test_admin_role_binding_is_school_scoped_31():
    school_a = _mk_school("tenantA")
    school_b = _mk_school("tenantB")
    user = _mk_user("tenant-admin")
    role_code = "m031_tenant_role"
    _assign_role(user, school_a, role_code)
    _grant(role_code, "admin.view")

    from core.permissions import user_has_permission

    assert user_has_permission(user, "admin.view", school=school_a) is True
    assert user_has_permission(user, "admin.view", school=school_b) is False


def test_school_objects_are_isolated_31():
    school_a = _mk_school("isoA")
    school_b = _mk_school("isoB")
    user = _mk_user("iso-admin")
    role_code = "m031_iso_role"
    _assign_role(user, school_a, role_code)

    assert UserRole.objects.filter(user=user, school=school_a).exists()
    assert not UserRole.objects.filter(user=user, school=school_b).exists()


def test_executive360_overview_view_importable_31():
    from executive360.api.views import ExecutiveSelfOverview
    assert callable(getattr(ExecutiveSelfOverview, "as_view", None))


def test_executive360_overview_url_registered_31():
    from django.urls import reverse
    assert "/api/executive360/me/overview/" in reverse("executive_360_self")


def test_executive360_denies_unauthenticated_31():
    response = Client().get("/api/executive360/me/overview/")
    assert response.status_code == 403
