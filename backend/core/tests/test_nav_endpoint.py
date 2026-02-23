# backend/core/tests/test_nav_endpoint.py
#
# Tests for GET /api/v1/nav/ (permission-derived navigation).
#
# The endpoint is served at /api/v1/nav/ (see api_urls.py).
# TenantHeaderRequiredMiddleware enforces X-School-Id for /api/v1/* routes and
# sets request.school; the nav view filters NAV_ITEMS by user permissions.

import json
import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _enable_tenant_middleware(settings):
    """Force TENANT_HEADER_REQUIRED=True for all nav tests.
    The root conftest.py disables it globally; these tests rely on the middleware.
    """
    settings.TENANT_HEADER_REQUIRED = True


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _school(name="Nav Test School"):
    # School has no slug field — just name.
    return School.objects.create(name=f"{name}-{uuid.uuid4()}")


def _user(label="u"):
    return UserAccount.objects.create_user(
        username=f"{label}-{uuid.uuid4()}",
        password="Passw0rd!",
    )


def _assign_role(user, school, role_code):
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code, defaults={"description": ""})
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def _nav_flat_labels(payload: dict) -> list[str]:
    """Flatten all item labels from /api/v1/nav/ response groups."""
    return [item["label"] for g in payload.get("groups", []) for item in g.get("items", [])]


def _nav_flat_hrefs(payload: dict) -> list[str]:
    """Flatten all item hrefs from /api/v1/nav/ response groups."""
    return [item["href"] for g in payload.get("groups", []) for item in g.get("items", [])]


# ──────────────────────────────────────────────────────────────────────────────
# Tenant enforcement
# ──────────────────────────────────────────────────────────────────────────────

class TestNavTenantEnforcement:

    def test_missing_school_id_header_returns_400(self):
        """Middleware must reject /api/v1/nav/ with no X-School-Id."""
        c = Client()
        r = c.get("/api/v1/nav/")
        assert r.status_code == 400

    def test_unknown_school_id_returns_404(self):
        """Middleware must reject an X-School-Id that doesn't resolve to a School."""
        c = Client()
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(uuid.uuid4()))
        assert r.status_code == 404


# ──────────────────────────────────────────────────────────────────────────────
# Permission filtering
# ──────────────────────────────────────────────────────────────────────────────

class TestNavPermissionFiltering:

    def test_parent_does_not_see_finance_admissions_billing_integrity(self):
        school = _school("Parent Nav School")
        parent = _user("parent1")
        _assign_role(parent, school, "parent")
        _grant("parent", "parent.view")

        c = Client()
        c.force_login(parent)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert r.status_code == 200

        payload = json.loads(r.content)
        labels = _nav_flat_labels(payload)
        hrefs = _nav_flat_hrefs(payload)

        assert "Parent" in labels
        assert "/parent" in hrefs

        # These must be absent
        assert "Finance" not in labels
        assert "Billing" not in labels
        assert "Admissions" not in labels
        assert "System Integrity" not in labels
        assert "/finance" not in hrefs
        assert "/billing" not in hrefs
        assert "/admissions" not in hrefs
        assert "/integrity" not in hrefs

    def test_finance_role_sees_finance_and_billing_not_admissions(self):
        school = _school("Finance Nav School")
        fin = _user("fin1")
        _assign_role(fin, school, "finance")
        _grant("finance", "finance.view")
        _grant("finance", "billing.view")

        c = Client()
        c.force_login(fin)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert r.status_code == 200

        payload = json.loads(r.content)
        hrefs = _nav_flat_hrefs(payload)

        assert "/finance" in hrefs
        assert "/billing" in hrefs
        assert "/admissions" not in hrefs
        assert "/parent" not in hrefs

    def test_head_of_school_sees_admin_board_integrity(self):
        school = _school("HoS Nav School")
        hos = _user("hos1")
        _assign_role(hos, school, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "admin.view")
        _grant("HEAD_OF_SCHOOL", "board.view")
        _grant("HEAD_OF_SCHOOL", "integrity.view")

        c = Client()
        c.force_login(hos)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert r.status_code == 200

        payload = json.loads(r.content)
        hrefs = _nav_flat_hrefs(payload)

        assert "/admin" in hrefs
        assert "/board" in hrefs
        assert "/integrity" in hrefs

    def test_user_with_no_roles_sees_empty_nav(self):
        school = _school("Empty Nav School")
        user = _user("noroles1")
        # No roles assigned, no permissions granted

        c = Client()
        c.force_login(user)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert r.status_code == 200

        payload = json.loads(r.content)
        assert payload["groups"] == []

    def test_teacher_sees_teacher_and_academics_not_finance(self):
        school = _school("Teacher Nav School")
        teacher = _user("teacher1")
        _assign_role(teacher, school, "TEACHER")
        _grant("TEACHER", "teacher.view")
        _grant("TEACHER", "academics.view")

        c = Client()
        c.force_login(teacher)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert r.status_code == 200

        payload = json.loads(r.content)
        hrefs = _nav_flat_hrefs(payload)

        assert "/teacher" in hrefs
        assert "/academics" in hrefs
        assert "/finance" not in hrefs
        assert "/admin" not in hrefs


# ──────────────────────────────────────────────────────────────────────────────
# Response shape
# ──────────────────────────────────────────────────────────────────────────────

class TestNavResponseShape:

    def test_response_has_groups_key(self):
        school = _school("Shape School")
        user = _user("shape1")
        _assign_role(user, school, "parent")
        _grant("parent", "parent.view")

        c = Client()
        c.force_login(user)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        payload = json.loads(r.content)

        assert "groups" in payload
        assert isinstance(payload["groups"], list)

    def test_group_has_title_and_items(self):
        school = _school("Shape School 2")
        user = _user("shape2")
        _assign_role(user, school, "parent")
        _grant("parent", "parent.view")

        c = Client()
        c.force_login(user)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        payload = json.loads(r.content)

        for group in payload["groups"]:
            assert "title" in group
            assert "items" in group
            assert isinstance(group["items"], list)

    def test_item_has_label_and_href(self):
        school = _school("Shape School 3")
        user = _user("shape3")
        _assign_role(user, school, "parent")
        _grant("parent", "parent.view")

        c = Client()
        c.force_login(user)
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        payload = json.loads(r.content)

        for group in payload["groups"]:
            for item in group["items"]:
                assert "label" in item
                assert "href" in item

    def test_school_scoping_cross_tenant_isolation(self):
        """User's role in school A must not grant nav in school B."""
        school_a = _school("School A Nav")
        school_b = _school("School B Nav")
        user = _user("cross")
        _assign_role(user, school_a, "finance")
        _grant("finance", "finance.view")

        c = Client()
        c.force_login(user)
        # Request against school_b — user has no role there
        r = c.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school_b.id))
        assert r.status_code == 200

        payload = json.loads(r.content)
        assert payload["groups"] == []
