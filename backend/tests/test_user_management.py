import uuid

import pytest
from django.db import IntegrityError, transaction

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from core.permissions import user_has_permission

pytestmark = pytest.mark.django_db

def _school(label="Module003"):
    return School.objects.create(name=f"{label}-{uuid.uuid4()}")

def _user(label="module003"):
    ident = uuid.uuid4()
    return UserAccount.objects.create_user(
        username=f"{label}-{ident}",
        email=f"{label}-{ident}@example.test",
        password="Passw0rd!",
    )

def _permission(code):
    perm, _ = CrownPermission.objects.get_or_create(
        code=code,
        defaults={"description": f"Module 003 test permission: {code}"},
    )
    return perm

def _grant(role_code, permission_code):
    perm = _permission(permission_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
    return perm

def _assign_role(user, school, role_code):
    return UserRole.objects.create(user=user, school=school, role_code=role_code)

class TestModule003UserCreationRoleAssignment:
    def test_user_creation_with_role_assignment_grants_scoped_permission(self):
        school = _school("Role Assignment")
        user = _user("registrar")
        _grant("REGISTRAR", "user_management.view")

        role = _assign_role(user, school, "REGISTRAR")

        assert role.user == user
        assert role.school == school
        assert role.role_code == "REGISTRAR"
        assert user_has_permission(user, "user_management.view", school=school) is True

    def test_role_assignment_does_not_bleed_across_tenants(self):
        school_a = _school("Tenant A")
        school_b = _school("Tenant B")
        user = _user("tenant-scoped")
        _grant("REGISTRAR", "user_management.view")

        _assign_role(user, school_a, "REGISTRAR")

        assert user_has_permission(user, "user_management.view", school=school_a) is True
        assert user_has_permission(user, "user_management.view", school=school_b) is False

class TestModule003RoleTransitions:
    def test_role_change_workflow_removes_old_permission_and_adds_new_permission(self):
        school = _school("Role Transition")
        user = _user("transition")
        _grant("TEACHER", "teacher.portal.view")
        _grant("REGISTRAR", "user_management.view")

        role = _assign_role(user, school, "TEACHER")

        assert user_has_permission(user, "teacher.portal.view", school=school) is True
        assert user_has_permission(user, "user_management.view", school=school) is False

        role.role_code = "REGISTRAR"
        role.save(update_fields=["role_code", "updated_at"])

        assert user_has_permission(user, "teacher.portal.view", school=school) is False
        assert user_has_permission(user, "user_management.view", school=school) is True

    def test_user_can_hold_distinct_roles_in_distinct_tenants_without_cross_bleed(self):
        school_a = _school("Multi Tenant A")
        school_b = _school("Multi Tenant B")
        user = _user("multi-tenant")
        _grant("REGISTRAR", "user_management.view")
        _grant("FINANCE_DIRECTOR", "billing.view")

        _assign_role(user, school_a, "REGISTRAR")
        _assign_role(user, school_b, "FINANCE_DIRECTOR")

        assert user_has_permission(user, "user_management.view", school=school_a) is True
        assert user_has_permission(user, "billing.view", school=school_a) is False
        assert user_has_permission(user, "billing.view", school=school_b) is True
        assert user_has_permission(user, "user_management.view", school=school_b) is False

class TestModule003RoleDeactivation:
    def test_deleted_role_can_no_longer_act(self):
        school = _school("Role Deactivation")
        user = _user("deactivate")
        _grant("REGISTRAR", "user_management.view")

        role = _assign_role(user, school, "REGISTRAR")

        assert user_has_permission(user, "user_management.view", school=school) is True

        role.delete()

        assert user_has_permission(user, "user_management.view", school=school) is False

class TestModule003BulkRoleOperations:
    def test_bulk_role_assignment_to_user_cohort(self):
        school = _school("Bulk Assignment")
        users = [_user(f"bulk-{i}") for i in range(3)]
        _grant("TEACHER", "teacher.portal.view")

        UserRole.objects.bulk_create([
            UserRole(school=school, user=user, role_code="TEACHER")
            for user in users
        ])

        assert UserRole.objects.filter(school=school, role_code="TEACHER").count() == 3

        for user in users:
            assert user_has_permission(user, "teacher.portal.view", school=school) is True

    def test_bulk_assignment_remains_tenant_scoped(self):
        school_a = _school("Bulk Tenant A")
        school_b = _school("Bulk Tenant B")
        users = [_user(f"bulk-tenant-{i}") for i in range(2)]
        _grant("TEACHER", "teacher.portal.view")

        UserRole.objects.bulk_create([
            UserRole(school=school_a, user=user, role_code="TEACHER")
            for user in users
        ])

        for user in users:
            assert user_has_permission(user, "teacher.portal.view", school=school_a) is True
            assert user_has_permission(user, "teacher.portal.view", school=school_b) is False

class TestModule003RoleTenantUniqueness:
    def test_duplicate_role_for_same_user_school_and_role_is_rejected(self):
        school = _school("Unique Constraint")
        user = _user("unique")
        _assign_role(user, school, "REGISTRAR")

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                _assign_role(user, school, "REGISTRAR")

    def test_same_user_can_have_same_role_in_different_schools(self):
        school_a = _school("Unique A")
        school_b = _school("Unique B")
        user = _user("same-role-different-schools")

        _assign_role(user, school_a, "REGISTRAR")
        _assign_role(user, school_b, "REGISTRAR")

        assert UserRole.objects.filter(user=user, role_code="REGISTRAR").count() == 2

    def test_same_user_can_have_different_roles_in_same_school(self):
        school = _school("Multi Role Same Tenant")
        user = _user("different-roles")

        _assign_role(user, school, "REGISTRAR")
        _assign_role(user, school, "FINANCE_DIRECTOR")

        assert set(
            UserRole.objects.filter(user=user, school=school).values_list("role_code", flat=True)
        ) == {"REGISTRAR", "FINANCE_DIRECTOR"}
