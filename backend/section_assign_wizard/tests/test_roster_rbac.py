import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.management.commands.seed_permissions import PERMISSIONS, ROLE_PERMISSIONS
from core.models import CrownPermission, RolePermission, School, UserRole
from households.models import Household, Student
from section_assign_wizard.models import SectionAssignWizardSession


pytestmark = pytest.mark.django_db

BASE_URL = "/api/v1/section-assign-wizard/sessions/"


def _school(name="Roster RBAC School"):
    return School.objects.create(name=f"{name} {uuid.uuid4().hex[:6]}")


def _user():
    User = get_user_model()
    return User.objects.create_user(
        username=f"roster-rbac-{uuid.uuid4().hex[:10]}",
        password="TestOnly-Roster-RBAC-123!",
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _headers(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


def _grant(user, school, role_code, *permission_codes):
    UserRole.objects.create(school=school, user=user, role_code=role_code)
    for code in permission_codes:
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": f"test permission {code}"},
        )
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _section(school):
    course = Course.objects.create(
        school_id=school.id,
        code=f"RBAC-{uuid.uuid4().hex[:8]}",
        name="Roster RBAC Course",
    )
    return Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )


def _student(school):
    household = Household.objects.create(
        school_id=school.id,
        name=f"Roster Household {uuid.uuid4().hex[:6]}",
    )
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Roster",
        last_name=f"Student{uuid.uuid4().hex[:4]}",
    )


def _staged_session(*, school, user, section, student):
    return SectionAssignWizardSession.objects.create(
        school=school,
        created_by=user,
        section_id=section.id,
        term=section.term,
        student_pool=[str(student.id)],
        roster_changes=[{"student_id": str(student.id), "action": "add"}],
        status=SectionAssignWizardSession.STATUS_ROSTER_STAGED,
    )


def test_seed_registry_defines_narrow_roster_edit_authority():
    permission_codes = {code for code, _ in PERMISSIONS}
    assert "rosters.edit" in permission_codes

    expected_roles = {
        "HEAD_OF_SCHOOL",
        "REGISTRAR",
        "head_of_school",
        "registrar",
        "school_admin",
    }
    actual_roles = {
        role for role, permissions in ROLE_PERMISSIONS.items() if "rosters.edit" in permissions
    }
    assert actual_roles == expected_roles
    assert "rosters.edit" not in ROLE_PERMISSIONS["TEACHER"]
    assert "rosters.edit" not in ROLE_PERMISSIONS["teacher"]


def test_create_session_requires_authentication():
    school = _school()
    response = APIClient().post(BASE_URL, **_headers(school))
    assert response.status_code == 401
    assert SectionAssignWizardSession.objects.count() == 0


def test_authenticated_user_without_roster_permission_cannot_create_session():
    school = _school()
    user = _user()
    response = _client(user).post(BASE_URL, **_headers(school))
    assert response.status_code == 403
    assert SectionAssignWizardSession.objects.count() == 0


@pytest.mark.parametrize("role_code", ["REGISTRAR", "HEAD_OF_SCHOOL"])
def test_authorized_roster_management_roles_can_create_session(role_code):
    school = _school()
    user = _user()
    _grant(user, school, role_code, "rosters.edit")

    response = _client(user).post(BASE_URL, **_headers(school))

    assert response.status_code == 201
    session = SectionAssignWizardSession.objects.get(id=response.data["session_id"])
    assert session.school_id == school.id
    assert session.created_by_id == user.id


def test_teacher_legacy_academics_edit_does_not_grant_roster_mutation():
    school = _school()
    user = _user()
    _grant(user, school, "TEACHER", "academics.view", "academics.edit")

    response = _client(user).post(BASE_URL, **_headers(school))

    assert response.status_code == 403
    assert SectionAssignWizardSession.objects.count() == 0


def test_role_in_another_school_does_not_authorize_roster_mutation():
    school_a = _school("Authority School")
    school_b = _school("Target School")
    user = _user()
    _grant(user, school_a, "REGISTRAR", "rosters.edit")

    response = _client(user).post(BASE_URL, **_headers(school_b))

    assert response.status_code == 403
    assert SectionAssignWizardSession.objects.count() == 0


def test_revoked_role_is_rechecked_at_commit_and_writes_nothing():
    school = _school()
    user = _user()
    _grant(user, school, "REGISTRAR", "rosters.edit")
    section = _section(school)
    student = _student(school)
    session = _staged_session(
        school=school,
        user=user,
        section=section,
        student=student,
    )

    UserRole.objects.filter(user=user, school=school, role_code="REGISTRAR").delete()

    response = _client(user).post(
        f"{BASE_URL}{session.id}/commit/",
        {"confirm": True},
        format="json",
        **_headers(school),
    )

    assert response.status_code == 403
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_ROSTER_STAGED
    assert Enrollment.objects.filter(section=section, student=student).count() == 0


def test_verify_uses_tenant_scoped_academics_view_authority():
    school = _school()
    user = _user()
    _grant(user, school, "TEACHER", "academics.view")
    section = _section(school)
    session = SectionAssignWizardSession.objects.create(
        school=school,
        created_by=user,
        section_id=section.id,
        term=section.term,
        status=SectionAssignWizardSession.STATUS_COMMITTED,
        commit_result={"enrolled": 0, "removed": 0},
    )

    response = _client(user).get(
        f"{BASE_URL}{session.id}/verify/",
        **_headers(school),
    )

    assert response.status_code == 200
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_VERIFIED


def test_authorized_repeated_commit_remains_idempotent():
    school = _school()
    user = _user()
    _grant(user, school, "REGISTRAR", "rosters.edit")
    section = _section(school)
    student = _student(school)
    session = _staged_session(
        school=school,
        user=user,
        section=section,
        student=student,
    )
    client = _client(user)
    url = f"{BASE_URL}{session.id}/commit/"

    first = client.post(url, {"confirm": True}, format="json", **_headers(school))
    second = client.post(url, {"confirm": True}, format="json", **_headers(school))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.data["enrolled"] == 1
    assert second.data["enrolled"] == 1
    assert Enrollment.objects.filter(section=section, student=student).count() == 1
