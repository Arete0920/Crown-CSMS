import pytest
from django.contrib.auth import get_user_model

from core.models import School, UserRole
from crown_api.tenant import (
    principal_can_override_tenant,
    principal_can_select_tenant,
)

pytestmark = pytest.mark.django_db


def test_principal_can_select_direct_school():
    school = School.objects.create(name="Direct Tenant")
    user = get_user_model().objects.create_user(
        username="direct-tenant-user",
        password="test-only-password",
        school=school,
    )
    assert principal_can_select_tenant(user, school.id) is True


def test_principal_can_select_assigned_role_school():
    school = School.objects.create(name="Role Tenant")
    user = get_user_model().objects.create_user(
        username="role-tenant-user",
        password="test-only-password",
    )
    UserRole.objects.create(user=user, school=school, role_code="AID_DIRECTOR")
    assert principal_can_select_tenant(user, school.id) is True


def test_principal_cannot_select_unassigned_school():
    assigned = School.objects.create(name="Assigned Tenant")
    other = School.objects.create(name="Other Tenant")
    user = get_user_model().objects.create_user(
        username="unassigned-tenant-user",
        password="test-only-password",
    )
    UserRole.objects.create(user=user, school=assigned, role_code="AID_DIRECTOR")
    assert principal_can_select_tenant(user, other.id) is False


def test_support_role_can_override_tenant():
    home = School.objects.create(name="Support Home")
    other = School.objects.create(name="Support Target")
    user = get_user_model().objects.create_user(
        username="support-tenant-user",
        password="test-only-password",
        school=home,
    )
    UserRole.objects.create(user=user, school=home, role_code="SUPPORT")
    assert principal_can_override_tenant(user) is True
    assert principal_can_select_tenant(user, other.id) is False
