import json
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import CrownPermission, RolePermission, School, UserRole
from households.models import Household, Student
from section_assign_wizard.models import SectionAssignWizardSession

pytestmark = pytest.mark.django_db
User = get_user_model()


def _student(school, suffix):
    household = Household.objects.create(school_id=school.id, name=f"Household {suffix}")
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Student",
        last_name=suffix,
    )


def _section(school, code):
    course = Course.objects.create(school_id=school.id, code=code, name=code)
    return Section.objects.create(school_id=school.id, course=course, term="FALL")


def _grant_wizard_access(user, school):
    UserRole.objects.get_or_create(user=user, school=school, role_code="REGISTRAR")
    for code in ("rosters.edit", "academics.view"):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": f"test permission {code}"},
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)


def _user(school, suffix):
    user = User.objects.create_user(
        username=f"user-{suffix}-{uuid.uuid4()}",
        password="pass12345!",
        school=school,
    )
    _grant_wizard_access(user, school)
    return user


def test_legacy_enroll_rejects_cross_school_section_without_persistence():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    section_b = _section(school_b, "B-101")
    student_a = _student(school_a, "A")
    client = Client()
    client.force_login(_user(school_a, "a"))

    response = client.post(
        "/api/v1/academics/enroll/",
        data=json.dumps({"section_id": str(section_b.id), "student_id": str(student_a.id)}),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )

    assert response.status_code == 404
    assert Enrollment.objects.count() == 0


def test_legacy_enroll_rejects_cross_school_student_without_persistence():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    section_a = _section(school_a, "A-101")
    student_b = _student(school_b, "B")
    client = Client()
    client.force_login(_user(school_a, "a"))

    response = client.post(
        "/api/v1/academics/enroll/",
        data=json.dumps({"section_id": str(section_a.id), "student_id": str(student_b.id)}),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )

    assert response.status_code == 404
    assert Enrollment.objects.count() == 0


def test_section_assign_wizard_rejects_cross_school_student_without_persistence():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    section_a = _section(school_a, "A-101")
    student_b = _student(school_b, "B")
    user = _user(school_a, "a")
    session = SectionAssignWizardSession.objects.create(
        school=school_a,
        created_by=user,
        section_id=section_a.id,
        term="FALL",
        student_pool=[str(student_b.id)],
        roster_changes=[{"student_id": str(student_b.id), "action": "add"}],
        status=SectionAssignWizardSession.STATUS_ROSTER_STAGED,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v1/section-assign-wizard/sessions/{session.id}/commit/",
        {"confirm": True},
        format="json",
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )

    assert response.status_code == 404
    assert Enrollment.objects.count() == 0
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_ROSTER_STAGED


def test_section_assign_wizard_commits_same_school_student():
    school = School.objects.create(name="School A")
    section = _section(school, "A-101")
    student = _student(school, "A")
    user = _user(school, "a")
    session = SectionAssignWizardSession.objects.create(
        school=school,
        created_by=user,
        section_id=section.id,
        term="FALL",
        student_pool=[str(student.id)],
        roster_changes=[{"student_id": str(student.id), "action": "add"}],
        status=SectionAssignWizardSession.STATUS_ROSTER_STAGED,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v1/section-assign-wizard/sessions/{session.id}/commit/",
        {"confirm": True},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    assert response.data["enrolled"] == 1
    assert Enrollment.objects.filter(
        school_id=school.id,
        section=section,
        student=student,
    ).exists()


def test_legacy_roster_enroll_denies_authenticated_parent_in_same_school():
    school = School.objects.create(name="Roster Authorization School")
    section = _section(school, "R-101")
    student = _student(school, "AuthorizedStudent")
    user = User.objects.create_user(
        username=f"parent-{uuid.uuid4()}", password="pass12345!", school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code="PARENT")
    client = Client()
    client.force_login(user)

    response = client.post(
        "/api/v1/academics/enroll/",
        data=json.dumps({"section_id": str(section.id), "student_id": str(student.id)}),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403
    assert response.json()["ok"] is False
    assert Enrollment.objects.filter(school_id=school.id, section=section, student=student).count() == 0


def test_legacy_roster_enroll_denies_unrelated_school_permission():
    school = School.objects.create(name="Roster Teacher Scope School")
    section = _section(school, "R-201")
    student = _student(school, "StudentA")
    user = User.objects.create_user(
        username=f"teacher-{uuid.uuid4()}", password="pass12345!", school=school,
    )
    role_code = "ACADEMICS_ONLY_ROSTER_TEST"
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(
        code="academics.edit",
        defaults={"description": "Edit academic work, not classroom membership"},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    client = Client()
    client.force_login(user)

    response = client.post(
        "/api/v1/academics/enroll/",
        data=json.dumps({"section_id": str(section.id), "student_id": str(student.id)}),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403
    assert Enrollment.objects.filter(school_id=school.id, section=section, student=student).count() == 0


def test_legacy_roster_enroll_allows_explicit_registrar_and_is_idempotent():
    school = School.objects.create(name="Roster Authorized School")
    section = _section(school, "R-301")
    student = _student(school, "StudentA")
    client = Client()
    client.force_login(_user(school, "registrar"))
    payload = json.dumps({"section_id": str(section.id), "student_id": str(student.id)})

    first = client.post(
        "/api/v1/academics/enroll/", data=payload, content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    second = client.post(
        "/api/v1/academics/enroll/", data=payload, content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert first.status_code == 201, first.content
    assert second.status_code == 201, second.content
    assert first.json()["data"]["enrollment_id"] == second.json()["data"]["enrollment_id"]
    assert Enrollment.objects.filter(school_id=school.id, section=section, student=student).count() == 1


def test_legacy_roster_enroll_rejects_disabled_school_even_with_registrar_grant():
    school = School.objects.create(name="Inactive School", is_active=False)
    section = _section(school, "R-401")
    student = _student(school, "StudentA")
    client = Client()
    client.force_login(_user(school, "registrar"))
    response = client.post(
        "/api/v1/academics/enroll/",
        data=json.dumps({"section_id": str(section.id), "student_id": str(student.id)}),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    # Tenant scoping rejects an inactive school as unknown (404) before
    # roster RBAC is evaluated; both layers must remain fail-closed.
    assert response.status_code == 404
    assert not Enrollment.objects.filter(school_id=school.id, section=section, student=student).exists()
