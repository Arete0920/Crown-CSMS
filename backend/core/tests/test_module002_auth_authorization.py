# backend/core/tests/test_module002_auth_authorization.py
"""Module 002 — Authentication & Authorization proof coverage.

This file intentionally layers focused certification tests on top of the generic
permission-engine tests. It proves the module-level behavior required for CROWN's
identity, role, permission, and tenant/school authorization backbone.
"""

import json
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory

from core.models import CrownPermission, RolePermission, School, UserRole
from core.permissions import CrownModulePermission, require_permission, user_has_permission

pytestmark = pytest.mark.django_db

User = get_user_model()


def _school(name="Module 002 Academy"):
    return School.objects.create(name=name)


def _user(label="module002"):
    return User.objects.create_user(
        username=f"{label}-{uuid.uuid4()}",
        email=f"{label}-{uuid.uuid4()}@example.test",
        password="Passw0rd!",
    )


def _assign_role(user, school, role_code):
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


def _seed_permissions():
    call_command("seed_permissions")


class TestModule002PermissionSeedContract:
    def test_seed_registers_identity_and_authorization_backbone_permissions(self):
        _seed_permissions()

        expected_codes = {
            "admin.view",
            "security.view",
            "integrity.view",
            "director.actions",
            "metrics.view",
        }

        assert set(
            CrownPermission.objects.filter(code__in=expected_codes).values_list("code", flat=True)
        ) == expected_codes

    def test_seed_maps_privileged_roles_without_granting_teacher_director_authority(self):
        _seed_permissions()

        assert RolePermission.objects.filter(
            role_code="HEAD_OF_SCHOOL",
            permission__code="director.actions",
        ).exists()
        assert RolePermission.objects.filter(
            role_code="FINANCE_DIRECTOR",
            permission__code="director.actions",
        ).exists()
        assert not RolePermission.objects.filter(
            role_code="TEACHER",
            permission__code="director.actions",
        ).exists()


class TestModule002TenantScopedAuthorization:
    def test_permission_grant_is_scoped_to_the_requested_school(self):
        _seed_permissions()
        school_a = _school("Scoped School A")
        school_b = _school("Scoped School B")
        user = _user("scoped-admin")

        _assign_role(user, school_a, "TEACHER")
        _assign_role(user, school_b, "HEAD_OF_SCHOOL")

        assert user_has_permission(user, "director.actions", school=school_b) is True
        assert user_has_permission(user, "director.actions", school=school_a) is False

    def test_cross_school_role_does_not_authorize_drf_module_permission(self):
        _seed_permissions()
        school_a = _school("DRF School A")
        school_b = _school("DRF School B")
        user = _user("drf-cross-school")
        _assign_role(user, school_a, "HEAD_OF_SCHOOL")

        permission = CrownModulePermission("admin.view")()
        request = RequestFactory().get("/api/v1/admin/")
        request.user = user
        request.school = school_b

        assert permission.has_permission(request, view=None) is False


class TestModule002RequestAuthorizationGuards:
    def test_crown_module_permission_requires_authenticated_user_school_and_permission(self):
        _seed_permissions()
        school = _school("Request Guard School")
        admin = _user("request-admin")
        teacher = _user("request-teacher")
        _assign_role(admin, school, "HEAD_OF_SCHOOL")
        _assign_role(teacher, school, "TEACHER")

        permission = CrownModulePermission("admin.view", write_code="director.actions")()

        read_request = RequestFactory().get("/api/v1/admin/")
        read_request.user = admin
        read_request.school = school
        assert permission.has_permission(read_request, view=None) is True

        write_request = RequestFactory().post("/api/v1/admin/")
        write_request.user = teacher
        write_request.school = school
        assert permission.has_permission(write_request, view=None) is False

        no_school_request = RequestFactory().get("/api/v1/admin/")
        no_school_request.user = admin
        assert permission.has_permission(no_school_request, view=None) is False

    def test_require_permission_denies_without_executing_protected_view(self):
        _seed_permissions()
        school = _school("Decorator Guard School")
        teacher = _user("decorator-teacher")
        admin = _user("decorator-admin")
        _assign_role(teacher, school, "TEACHER")
        _assign_role(admin, school, "HEAD_OF_SCHOOL")

        side_effects = []

        @require_permission("director.actions")
        def protected_view(request):
            side_effects.append("executed")
            return HttpResponse("ok", status=200)

        denied_request = RequestFactory().post("/api/v1/protected/")
        denied_request.user = teacher
        denied_request.school = school
        denied_response = protected_view(denied_request)

        assert denied_response.status_code == 403
        assert json.loads(denied_response.content) == {"detail": "Permission denied."}
        assert side_effects == []

        allowed_request = RequestFactory().post("/api/v1/protected/")
        allowed_request.user = admin
        allowed_request.school = school
        allowed_response = protected_view(allowed_request)

        assert allowed_response.status_code == 200
        assert side_effects == ["executed"]
