"""School-scoped camp permission provisioning regression tests."""
import importlib

import pytest
from django.apps import apps

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from core.permissions import user_has_permission
from core.management.commands.seed_permissions import PERMISSIONS, ROLE_PERMISSIONS


pytestmark = pytest.mark.django_db


def test_camp_permissions_migrate_idempotently_without_granting_ordinary_staff():
    migration = importlib.import_module("core.migrations.0019_seed_summer_camp_permissions")
    migration.seed_summer_camp_permissions(apps, None)
    migration.seed_summer_camp_permissions(apps, None)
    school = School.objects.create(name="Camp RBAC School")
    other_school = School.objects.create(name="Unrelated Camp RBAC School")

    authorized = UserAccount.objects.create_user(
        username="camp-permission-owner", school=school, password="synthetic-test",
    )
    UserRole.objects.create(user=authorized, school=school, role_code="HEAD_OF_SCHOOL")
    for permission_code, _description in migration.CAMP_PERMISSIONS:
        assert CrownPermission.objects.filter(code=permission_code).count() == 1
        assert RolePermission.objects.filter(
            permission__code=permission_code,
            role_code__in=migration.DEFAULT_ROLES,
        ).count() == len(migration.DEFAULT_ROLES)
        assert user_has_permission(authorized, permission_code, school=school)
        assert not user_has_permission(authorized, permission_code, school=other_school)

        ungranted_staff = UserAccount.objects.create_user(
            username="camp-permission-staff-" + permission_code.replace(".", "-"),
            school=school, is_staff=True, password="synthetic-test",
        )
        assert not user_has_permission(ungranted_staff, permission_code, school=school)
        assert not RolePermission.objects.filter(
            permission__code=permission_code, role_code__in=("SUPPORT", "TEACHER", "PARENT"),
        ).exists()


def test_standard_permission_seed_keeps_camp_roles_available():
    defined = dict(PERMISSIONS)
    for permission_code in ("summer_camp.view", "summer_camp.edit"):
        assert permission_code in defined
        for role in ("HEAD_OF_SCHOOL", "head_of_school", "school_admin"):
            assert permission_code in ROLE_PERMISSIONS[role]
        assert permission_code not in ROLE_PERMISSIONS["SUPPORT"]
        assert permission_code not in ROLE_PERMISSIONS["PARENT"]
