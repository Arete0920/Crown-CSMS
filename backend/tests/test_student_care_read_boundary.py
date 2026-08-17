from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.management.commands.seed_permissions import PERMISSIONS, ROLE_PERMISSIONS
from core.models import (
    CrownPermission,
    Family,
    RolePermission,
    School,
    Student,
    UserRole,
)
from discipline.models import DisciplineAction, DisciplineIncident


User = get_user_model()
pytestmark = pytest.mark.django_db

INCIDENTS_URL = "/api/discipline/incidents/"
METRICS_URL = "/api/discipline/metrics/"
STUDENT_CARE_CODES = {
    "student-care.view",
    "student-care.view_restricted",
    "student-care.create",
    "student-care.edit",
    "student-care.close",
    "student-care.export",
}
RESTRICTED_DETAIL_FIELDS = {
    "details",
    "parent_notified",
    "parent_notified_at",
    "reported_by",
    "assigned_to",
    "actions",
}


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _student(school: School) -> Student:
    family = Family.objects.create(
        school=school,
        family_name=f"Family {uuid.uuid4().hex[:8]}",
    )
    return Student.objects.create(
        school=school,
        family=family,
        first_name="Student",
        last_name="Care",
        dob="2010-01-15",
    )


def _user(prefix: str, school: School, *, is_staff: bool = False):
    user = User.objects.create_user(
        username=f"{prefix}_{uuid.uuid4().hex[:8]}",
        password="StudentCare-Test-Only",
        is_staff=is_staff,
    )
    UserRole.objects.create(
        user=user,
        school=school,
        role_code=f"{prefix}_{uuid.uuid4().hex[:8]}",
    )
    return user


def _grant(user, school: School, *codes: str) -> None:
    role = UserRole.objects.filter(user=user, school=school).first()
    assert role is not None
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(
            role_code=role.role_code,
            permission=permission,
        )


def _client(user, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _incident(school: School, student: Student, actor) -> DisciplineIncident:
    incident = DisciplineIncident.objects.create(
        school=school,
        student=student,
        reported_by=actor,
        occurred_at=timezone.now(),
        location="Counseling Office",
        category="behavior",
        severity="major",
        status="open",
        summary="Restricted Student Care summary",
        details="Restricted Student Care detail",
        parent_notified=True,
        parent_notified_at=timezone.now(),
    )
    DisciplineAction.objects.create(
        incident=incident,
        actor=actor,
        action_type="note",
        note="Restricted action note",
    )
    return incident


def test_registry_contains_all_canonical_student_care_permissions():
    registered = {code for code, _description in PERMISSIONS}
    assert STUDENT_CARE_CODES <= registered
    assert STUDENT_CARE_CODES <= set(ROLE_PERMISSIONS["HEAD_OF_SCHOOL"])
    assert STUDENT_CARE_CODES <= set(ROLE_PERMISSIONS["head_of_school"])


def test_authenticated_user_without_student_care_view_cannot_list_incidents():
    school = _school("No Student Care")
    user = _user("ordinary", school)
    response = _client(user, school).get(INCIDENTS_URL)
    assert response.status_code == 403


def test_django_staff_flag_does_not_bypass_student_care_permission():
    school = _school("Staff Flag")
    user = _user("staff", school, is_staff=True)
    response = _client(user, school).get(INCIDENTS_URL)
    assert response.status_code == 403


def test_student_care_view_allows_list_and_metrics_but_redacts_list_state():
    school = _school("View Grant")
    user = _user("viewer", school)
    _grant(user, school, "student-care.view")
    incident = _incident(school, _student(school), user)

    list_response = _client(user, school).get(INCIDENTS_URL)
    assert list_response.status_code == 200
    row = next(item for item in list_response.data if str(item["id"]) == str(incident.id))
    assert "parent_notified" not in row
    assert _client(user, school).get(METRICS_URL).status_code == 200


def test_student_care_view_redacts_restricted_detail_fields():
    school = _school("Redacted Detail")
    user = _user("viewer", school)
    _grant(user, school, "student-care.view")
    incident = _incident(school, _student(school), user)

    response = _client(user, school).get(f"{INCIDENTS_URL}{incident.id}/")

    assert response.status_code == 200
    assert RESTRICTED_DETAIL_FIELDS.isdisjoint(response.data.keys())
    assert response.data["summary"] == incident.summary
    assert response.data["student"] == incident.student_id


def test_restricted_permission_exposes_restricted_detail_and_action_notes():
    school = _school("Restricted Detail")
    user = _user("restricted", school)
    _grant(
        user,
        school,
        "student-care.view",
        "student-care.view_restricted",
    )
    incident = _incident(school, _student(school), user)

    response = _client(user, school).get(f"{INCIDENTS_URL}{incident.id}/")

    assert response.status_code == 200
    assert RESTRICTED_DETAIL_FIELDS <= set(response.data.keys())
    assert response.data["details"] == incident.details
    assert response.data["actions"][0]["note"] == "Restricted action note"


def test_restricted_permission_exposes_parent_notification_on_list():
    school = _school("Restricted List")
    user = _user("restricted_list", school)
    _grant(user, school, "student-care.view", "student-care.view_restricted")
    incident = _incident(school, _student(school), user)

    response = _client(user, school).get(INCIDENTS_URL)

    assert response.status_code == 200
    row = next(item for item in response.data if str(item["id"]) == str(incident.id))
    assert row["parent_notified"] is True


def test_view_permission_is_tenant_scoped_and_cannot_cross_school():
    school_a = _school("Tenant A")
    school_b = _school("Tenant B")
    user = _user("tenant_a_viewer", school_a)
    _grant(user, school_a, "student-care.view", "student-care.view_restricted")
    incident_b = _incident(school_b, _student(school_b), None)

    response = _client(user, school_a).get(f"{INCIDENTS_URL}{incident_b.id}/")

    assert response.status_code == 404


def test_metrics_requires_student_care_view_permission():
    school = _school("Metrics Boundary")
    user = _user("metrics_denied", school)
    response = _client(user, school).get(METRICS_URL)
    assert response.status_code == 403
