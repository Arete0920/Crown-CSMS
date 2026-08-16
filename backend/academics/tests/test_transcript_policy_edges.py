import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, Term, TranscriptEntry
from core.models import AcademicYear, School, UserRole
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _context():
    school = School.objects.create(name="Transcript Policy School")
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
        code="FALL",
        name="Fall",
        school_year=year.name,
        ordering=1,
        active=True,
    )
    household = Household.objects.create(school_id=school.id, name="Policy Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Policy",
        last_name="Student",
        grade_level="12",
    )
    User = get_user_model()
    registrar = User.objects.create_user(
        username=f"registrar-{uuid.uuid4()}",
        email=f"registrar-{uuid.uuid4()}@test.local",
        password="test-pass",
        school=school,
    )
    UserRole.objects.create(school=school, user=registrar, role_code="REGISTRAR")
    client = APIClient()
    client.force_authenticate(registrar)
    return school, term, student, client


def _add_course(*, school, term, student, code, letter, credit="1.00", gpa_points="0.00"):
    course = Course.objects.create(
        school_id=school.id,
        code=code,
        name=f"Course {code}",
        credits=credit,
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course,
        term=term,
        credit_value=credit,
        final_letter_grade=letter,
        gpa_points=gpa_points,
    )


def _snapshot(client, school, student):
    response = client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content
    return response.json()


def test_standard_letter_points_replace_unpopulated_zero_default_for_a_to_d():
    school, term, student, client = _context()
    _add_course(
        school=school,
        term=term,
        student=student,
        code="ENG-401",
        letter="A",
        gpa_points="0.00",
    )

    data = _snapshot(client, school, student)
    row = data["terms"][0]["courses"][0]
    assert row["gpa_points"] == "4.00"
    assert data["cumulative_gpa"] == "4.00"


def test_nonzero_final_gpa_points_is_explicit_weighting_override():
    school, term, student, client = _context()
    _add_course(
        school=school,
        term=term,
        student=student,
        code="HON-401",
        letter="A",
        gpa_points="4.50",
    )

    data = _snapshot(client, school, student)
    assert data["terms"][0]["courses"][0]["gpa_points"] == "4.50"
    assert data["cumulative_gpa"] == "4.50"


def test_pass_earns_credit_without_affecting_gpa():
    school, term, student, client = _context()
    _add_course(
        school=school,
        term=term,
        student=student,
        code="SERV-401",
        letter="P",
    )

    data = _snapshot(client, school, student)
    row = data["terms"][0]["courses"][0]
    assert row["attempted_credits"] == "1.00"
    assert row["earned_credits"] == "1.00"
    assert row["gpa_included"] is False
    assert data["cumulative_gpa"] is None


@pytest.mark.parametrize("mark", ["I", "W"])
def test_incomplete_and_withdrawn_are_excluded_from_credit_and_gpa_totals(mark):
    school, term, student, client = _context()
    _add_course(
        school=school,
        term=term,
        student=student,
        code=f"EDGE-{mark}",
        letter=mark,
    )

    data = _snapshot(client, school, student)
    row = data["terms"][0]["courses"][0]
    assert row["attempted_credits"] == "0.00"
    assert row["earned_credits"] == "0.00"
    assert row["gpa_included"] is False
    assert data["cumulative_gpa"] is None
