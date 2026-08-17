import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from safety.models import IncidentReport

pytestmark = pytest.mark.django_db

METRICS_URL = "/api/v1/safety/metrics/"
SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"


def _school(suffix):
    return School.objects.create(name=f"Safety Metrics Test {suffix}")


def _user(prefix, *, is_staff=False):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password="Passw0rd!",
        is_staff=is_staff,
    )


def _role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, permission_code="safety.view"):
    permission, _ = CrownPermission.objects.get_or_create(code=permission_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def test_safety_metrics_requires_safety_view_grant():
    school = _school("denied")
    user = _user("safety-denied")
    _role(user, school, "safety_metrics_no_grant")

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 403


def test_safety_metrics_django_staff_does_not_bypass_crown_permission():
    school = _school("staff-denied")
    user = _user("safety-staff-denied", is_staff=True)
    _role(user, school, "safety_metrics_staff_no_grant")

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 403


def test_safety_metrics_allows_safety_view_and_scopes_counts_to_tenant():
    school = _school("allowed")
    other_school = _school("other")
    user = _user("safety-allowed")
    role_code = "safety_metrics_allowed"
    _role(user, school, role_code)
    _grant(role_code)

    IncidentReport.objects.create(
        school_id=school.id,
        category="Weather",
        severity="high",
        description="Open local incident",
        resolved=False,
    )
    IncidentReport.objects.create(
        school_id=school.id,
        category="Facility",
        severity="low",
        description="Closed local incident",
        resolved=True,
    )
    IncidentReport.objects.create(
        school_id=other_school.id,
        category="Foreign",
        severity="critical",
        description="Foreign tenant incident",
        resolved=False,
    )

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert response.status_code == 200
    assert response.json() == {
        "total_incidents": 2,
        "open_incidents": 1,
        "closed_incidents": 1,
        "by_severity": [
            {"severity": "high", "count": 1},
            {"severity": "low", "count": 1},
        ],
        "by_status": [
            {"status": "open", "count": 1},
            {"status": "closed", "count": 1},
        ],
    }


def test_safety_metrics_rejects_cross_tenant_role_reuse():
    school = _school("role-school")
    other_school = _school("requested-school")
    user = _user("safety-cross-tenant")
    role_code = "safety_metrics_cross_tenant"
    _role(user, school, role_code)
    _grant(role_code)

    client = Client()
    client.force_login(user)
    response = client.get(METRICS_URL, **{SCHOOL_ID_HEADER: str(other_school.id)})

    assert response.status_code == 404


def test_safety_metrics_requires_tenant_context():
    user = _user("safety-no-tenant")
    client = Client()
    client.force_login(user)

    response = client.get(METRICS_URL)

    assert response.status_code in (400, 403)
