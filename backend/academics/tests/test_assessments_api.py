import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import AssignmentCategory, Course, Enrollment, Section, Term
from core.models import AcademicYear, School
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _mk_staff_user(school: School):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        password="pass12345!",
        school=school,
        is_staff=True,
    )
    return user


def _seed_section(*, school: School):
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall",
        school_year="2026-2027",
        ordering=1,
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code="SCI-101",
        name="Science 9",
        department="Science",
        credits="1.00",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
        teacher_name="Mrs. Smith",
    )
    household = Household.objects.create(school_id=school.id, name="Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Jane",
        last_name="Doe",
        grade_level="9",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    return section


def test_section_assessments_read_model():
    school = School.objects.create(name="Test School")
    user = _mk_staff_user(school)
    section = _seed_section(school=school)

    AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent="20.00",
        sort_order=1,
        is_active=True,
    )

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/assessments/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["section_id"] == str(section.id)
    assert body["assessments"], body
    row = body["assessments"][0]
    assert row["category"] == "Homework"
    assert row["weight"] == "20.00"
    assert row["published"] is True
