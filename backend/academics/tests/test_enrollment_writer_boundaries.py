import json
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import School
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


def _user(school, suffix):
    return User.objects.create_user(
        username=f"user-{suffix}-{uuid.uuid4()}",
        password="pass12345!",
        school=school,
    )


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
