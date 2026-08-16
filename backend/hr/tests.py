import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from hr.models import Employee

pytestmark = pytest.mark.django_db

METRICS_URL = "/api/v1/hr/metrics/"
SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"


def _school(suffix):
    return School.objects.create(name=f"HR Metrics Test {suffix}")


def _user(prefix):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password="Passw0rd!",
    )


def _role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, permission_code="hr.view"):
    permission, _ = CrownPermission.objects.get_or_create(code=permission_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def test_hr_metrics_requires_hr_view_grant():
    school = _school("denied")
    user = _user("hr-denied")
    _role(user, school, "hr_metrics_no_grant")

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 403


def test_hr_metrics_allows_hr_view_and_scopes_counts_to_tenant():
    school = _school("allowed")
    other_school = _school("other")
    user = _user("hr-allowed")
    role_code = "hr_metrics_allowed"
    _role(user, school, role_code)
    _grant(role_code)

    Employee.objects.create(
        school_id=school.id,
        first_name="Ada",
        last_name="Active",
        role="Teacher",
        department="Academics",
        active=True,
    )
    Employee.objects.create(
        school_id=school.id,
        first_name="Ina",
        last_name="Inactive",
        role="Aide",
        department="Academics",
        active=False,
    )
    Employee.objects.create(
        school_id=other_school.id,
        first_name="Other",
        last_name="Tenant",
        role="Teacher",
        department="Academics",
        active=True,
    )

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 200
    assert response.json() == {
        "total_employees": 2,
        "active_employees": 1,
        "inactive_employees": 1,
        "by_department": [{"department": "Academics", "count": 1}],
    }


def test_hr_metrics_rejects_cross_tenant_role_reuse():
    school = _school("role-school")
    other_school = _school("requested-school")
    user = _user("hr-cross-tenant")
    role_code = "hr_metrics_cross_tenant"
    _role(user, school, role_code)
    _grant(role_code)

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(other_school.id)})

    assert response.status_code == 404


def test_hr_metrics_requires_tenant_context():
    user = _user("hr-no-tenant")
    client = Client()
    client.force_login(user)

    response = client.get(METRICS_URL)

    assert response.status_code in (400, 403)
