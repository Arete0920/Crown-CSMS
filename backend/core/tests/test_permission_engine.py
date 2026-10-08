# backend/core/tests/test_permission_engine.py
#
# Tests for the Crown Central Permission Engine (Layer 1).
#
# Covers:
#   - user_has_permission() truth / denial / school scoping / anon
#   - require_permission() decorator  →  200 / 403 / 401 paths
#   - CrownPermission / RolePermission model integrity (unique constraints)
#   - seed_permissions management command idempotency

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from core.models import CrownPermission, RolePermission, School, UserRole
from core.permissions import require_permission, user_has_permission

pytestmark = pytest.mark.django_db

User = get_user_model()

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _school(name="Perm Test Academy"):
    return School.objects.create(name=name)


def _user(label="user"):
    return User.objects.create_user(username=f"{label}-{uuid.uuid4()}", password="Passw0rd!")


def _perm(code, description=""):
    obj, _ = CrownPermission.objects.get_or_create(code=code, defaults={"description": description})
    return obj


def _grant(role_code, permission_code):
    perm = _perm(permission_code)
    obj, _ = RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
    return obj


def _assign_role(user, school, role_code):
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


# ──────────────────────────────────────────────────────────────────────────────
# user_has_permission — basic grant / deny
# ──────────────────────────────────────────────────────────────────────────────

class TestUserHasPermission:

    def test_returns_true_when_role_granted(self):
        school = _school()
        user = _user("hos")
        _assign_role(user, school, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "finance.view")

        assert user_has_permission(user, "finance.view", school=school) is True

    def test_returns_false_when_role_not_granted(self):
        school = _school()
        user = _user("teacher")
        _assign_role(user, school, "TEACHER")
        _grant("HEAD_OF_SCHOOL", "finance.view")  # granted to HoS, not TEACHER

        assert user_has_permission(user, "finance.view") is False

    def test_returns_false_for_nonexistent_permission(self):
        school = _school()
        user = _user("hos2")
        _assign_role(user, school, "HEAD_OF_SCHOOL")

        assert user_has_permission(user, "nonexistent.code") is False

    def test_returns_false_when_user_has_no_roles(self):
        user = _user("noroles")
        _grant("HEAD_OF_SCHOOL", "finance.view")

        assert user_has_permission(user, "finance.view") is False

    def test_returns_false_for_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        _grant("HEAD_OF_SCHOOL", "finance.view")

        assert user_has_permission(anon, "finance.view") is False


# ──────────────────────────────────────────────────────────────────────────────
# user_has_permission — school scoping
# ──────────────────────────────────────────────────────────────────────────────

class TestUserHasPermissionSchoolScoping:

    def test_scoped_to_correct_school_returns_true(self):
        school = _school("School A")
        user = _user("hos-a")
        _assign_role(user, school, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "finance.view")

        assert user_has_permission(user, "finance.view", school=school) is True

    def test_scoped_to_wrong_school_returns_false(self):
        school_a = _school("School A2")
        school_b = _school("School B2")
        user = _user("hos-b")
        _assign_role(user, school_a, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "finance.view")

        # User has the role in school_a but we ask against school_b
        assert user_has_permission(user, "finance.view", school=school_b) is False

    def test_unscoped_query_cannot_combine_school_roles(self):
        school_a = _school("School A3")
        user = _user("crossschool")
        _assign_role(user, school_a, "FINANCE_DIRECTOR")
        _grant("FINANCE_DIRECTOR", "finance.edit")

        # Missing school context must fail closed.
        assert user_has_permission(user, "finance.edit") is False


# ──────────────────────────────────────────────────────────────────────────────
# require_permission decorator
# ──────────────────────────────────────────────────────────────────────────────

class TestRequirePermissionDecorator:

    def _make_view(self, perm_code):
        """Return a decorated dummy view that returns 200."""
        from django.http import HttpResponse

        @require_permission(perm_code)
        def dummy_view(request):
            return HttpResponse("ok", status=200)

        return dummy_view

    def test_allows_request_when_permission_granted(self):
        school = _school("Decorator School A")
        user = _user("dec-user-a")
        _assign_role(user, school, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "health.view")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user
        request.school = school

        view = self._make_view("health.view")
        response = view(request)
        assert response.status_code == 200

    def test_denies_request_when_permission_missing(self):
        school = _school("Decorator School B")
        user = _user("dec-user-b")
        _assign_role(user, school, "TEACHER")
        # TEACHER not granted finance.view

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user
        request.school = school

        view = self._make_view("finance.view")
        response = view(request)
        assert response.status_code == 403

    def test_denies_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser

        school = _school("Decorator School C")
        _grant("HEAD_OF_SCHOOL", "health.view")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = AnonymousUser()
        request.school = school

        view = self._make_view("health.view")
        response = view(request)
        assert response.status_code == 403

    def test_403_response_body_is_json(self):
        import json

        school = _school("Decorator School D")
        user = _user("dec-user-d")
        _assign_role(user, school, "TEACHER")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user
        request.school = school

        view = self._make_view("finance.edit")
        response = view(request)
        body = json.loads(response.content)
        assert body.get("detail") == "Permission denied."

    def test_no_request_school_attribute_does_not_crash(self):
        """An exempt route without school context cannot borrow another school's role."""
        school = _school("Decorator School E")
        user = _user("dec-user-e")
        _assign_role(user, school, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "metrics.view")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user
        # Intentionally NOT setting request.school

        view = self._make_view("metrics.view")
        response = view(request)
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Model constraints
# ──────────────────────────────────────────────────────────────────────────────

class TestPermissionModelConstraints:

    def test_crown_permission_code_is_unique(self):
        from django.db import IntegrityError

        _perm("duplicate.code")
        with pytest.raises(IntegrityError):
            CrownPermission.objects.create(code="duplicate.code")

    def test_role_permission_unique_together(self):
        from django.db import IntegrityError

        perm = _perm("unique.perm")
        RolePermission.objects.create(role_code="TEACHER", permission=perm)
        with pytest.raises(IntegrityError):
            RolePermission.objects.create(role_code="TEACHER", permission=perm)

    def test_crown_permission_str(self):
        perm = _perm("str.test", "A test permission")
        assert str(perm) == "str.test"

    def test_role_permission_str(self):
        perm = _perm("str.rp")
        rp = RolePermission.objects.create(role_code="TEACHER", permission=perm)
        assert str(rp) == "TEACHER → str.rp"


# ──────────────────────────────────────────────────────────────────────────────
# seed_permissions management command
# ──────────────────────────────────────────────────────────────────────────────

class TestSeedPermissionsCommand:

    def test_seed_creates_permissions(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("seed_permissions", stdout=out)
        assert CrownPermission.objects.filter(code="finance.view").exists()
        assert CrownPermission.objects.filter(code="director.actions").exists()

    def test_seed_creates_role_mappings(self):
        from django.core.management import call_command
        from io import StringIO
        call_command("seed_permissions", stdout=StringIO())
        assert RolePermission.objects.filter(
            role_code="HEAD_OF_SCHOOL",
            permission__code="finance.view",
        ).exists()
        assert RolePermission.objects.filter(
            role_code="FINANCE_DIRECTOR",
            permission__code="finance.edit",
        ).exists()

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        from io import StringIO
        call_command("seed_permissions", stdout=StringIO())
        count_before = CrownPermission.objects.count()
        call_command("seed_permissions", stdout=StringIO())
        count_after = CrownPermission.objects.count()
        assert count_before == count_after

    def test_seed_dry_run_creates_nothing(self):
        from django.core.management import call_command
        from io import StringIO
        permissions_before = CrownPermission.objects.count()
        mappings_before = RolePermission.objects.count()
        call_command("seed_permissions", dry_run=True, stdout=StringIO())
        assert CrownPermission.objects.count() == permissions_before
        assert RolePermission.objects.count() == mappings_before


def test_decorator_uses_explicit_tenant_header_without_middleware_school():
    school = _school("Header-scoped school")
    user = _user("header-scoped")
    _assign_role(user, school, "HEADER_VIEWER")
    _grant("HEADER_VIEWER", "finance.view")
    request = RequestFactory().get("/", HTTP_X_SCHOOL_ID=str(school.id))
    request.user = user
    from django.http import HttpResponse

    @require_permission("finance.view")
    def view(_request):
        return HttpResponse("ok")

    assert view(request).status_code == 200


def test_decorator_rejects_foreign_school_even_if_role_granted_elsewhere():
    school = _school("Granted tenant")
    foreign = _school("Unrelated tenant")
    user = _user("foreign-deny")
    _assign_role(user, school, "SCOPED_VIEWER")
    _grant("SCOPED_VIEWER", "finance.view")
    request = RequestFactory().get("/", HTTP_X_SCHOOL_ID=str(foreign.id))
    request.user = user
    from django.http import HttpResponse

    @require_permission("finance.view")
    def view(_request):
        return HttpResponse("ok")

    assert view(request).status_code == 403


def test_decorator_rejects_anonymous_and_missing_header_without_school():
    from django.contrib.auth.models import AnonymousUser
    from django.http import HttpResponse

    school = _school("No implicit selection")
    user = _user("no-selection")
    _assign_role(user, school, "NO_IMPLICIT_VIEW")
    _grant("NO_IMPLICIT_VIEW", "finance.view")

    @require_permission("finance.view")
    def view(_request):
        return HttpResponse("ok")

    missing = RequestFactory().get("/")
    missing.user = user
    assert view(missing).status_code == 403

    anonymous = RequestFactory().get("/", HTTP_X_SCHOOL_ID=str(school.id))
    anonymous.user = AnonymousUser()
    assert view(anonymous).status_code == 403
