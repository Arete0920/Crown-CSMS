"""
API tests for Transcript read-only and student-centric contracts.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, School, UserRole
from academics.models import Course, Enrollment, Section, Term, TranscriptEntry
from households.models import Household, Student
from gradebook.models import GradeEntry

pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str):
    User = get_user_model()
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )


def _assign_role(*, user, school: School, role_code: str):
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _seed_transcript_test_data(*, school: School):
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term1 = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall 2026",
        school_year="2026-2027",
        ordering=1,
        active=True,
    )
    term2 = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2027-SPRING",
        name="Spring 2027",
        school_year="2026-2027",
        ordering=2,
        active=True,
    )

    course1 = Course.objects.create(
        school_id=school.id,
        code="MATH-101",
        name="Mathematics",
        credits="0.50",
    )
    course2 = Course.objects.create(
        school_id=school.id,
        code="ELA-101",
        name="English Language Arts",
        credits="1.00",
    )

    section1 = Section.objects.create(
        school_id=school.id,
        course=course1,
        term=term1.code,
        term_ref=term1,
        teacher_name="Teacher A",
    )
    section2 = Section.objects.create(
        school_id=school.id,
        course=course2,
        term=term2.code,
        term_ref=term2,
        teacher_name="Teacher B",
    )

    household = Household.objects.create(school_id=school.id, name="Test Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name="Student",
        grade_level="3",
    )

    Enrollment.objects.create(school_id=school.id, section=section1, student=student)
    Enrollment.objects.create(school_id=school.id, section=section2, student=student)

    GradeEntry.objects.create(
        school_id=school.id,
        section=section1,
        student=student,
        assignment_name="Test 1",
        points_earned=90,
        points_possible=100,
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section2,
        student=student,
        assignment_name="Quiz 1",
        points_earned=80,
        points_possible=100,
    )

    return student


def test_transcript_ro_404_for_unknown_student():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="director@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        f"/api/v1/academics/transcript/{uuid.uuid4()}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 404


def test_transcript_ro_returns_terms_and_courses_for_demo_student():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="director@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")
    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content

    data = response.json()
    assert data["student"]["student_id"] == str(student.id)
    assert data["student"]["first_name"] == "Test"
    assert data["student"]["last_name"] == "Student"
    assert isinstance(data["terms"], list)
    assert len(data["terms"]) == 2

    term = data["terms"][0]
    assert "term_name" in term
    assert "term_gpa" in term
    assert "term_gpa_mvp" not in term
    assert term["courses"]

    course = term["courses"][0]
    for key in (
        "section_id",
        "course_code",
        "course_name",
        "teacher_name",
        "final_percent",
        "final_letter",
        "credits",
        "attempted_credits",
        "earned_credits",
        "gpa_points",
        "status",
        "grade_source",
        "credit_source",
    ):
        assert key in course

    assert "cumulative_gpa" in data
    assert "cumulative_gpa_mvp" not in data
    assert data["calculation_policy"]["in_progress_in_official_gpa"] is False


def test_transcript_ro_alias_returns_same_contract():
    school = School.objects.create(name="Alias School")
    user = _mk_user(school=school, email="alias-registrar@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")
    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        f"/api/v1/transcripts/students/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content
    assert response.json()["student"]["student_id"] == str(student.id)


def test_student_transcript_contract_shape():
    school = School.objects.create(name="Contract School")
    user = _mk_user(school=school, email="contract@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")
    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        f"/api/v1/academics/students/{student.id}/transcript/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content

    data = response.json()
    assert data["student_id"] == str(student.id)
    assert data["student_name"] == "Test Student"
    assert data["school_years"]
    assert "cumulative_gpa" in data
    assert "attempted_credits" in data
    assert "earned_credits" in data

    year = data["school_years"][0]
    term = year["terms"][0]
    course = term["courses"][0]
    assert "term_gpa" in term
    for key in (
        "section_id",
        "course_code",
        "course_name",
        "credits",
        "teacher",
        "final_grade",
        "final_percent",
        "gpa_points",
        "status",
    ):
        assert key in course


def test_transcript_ro_includes_dual_enrollment_metadata():
    school = School.objects.create(name="Metadata School")
    user = _mk_user(school=school, email="director-metadata@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")
    student = _seed_transcript_test_data(school=school)
    section = Section.objects.get(school_id=school.id, course__code="MATH-101")

    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=section.course,
        term=section.term_ref,
        credit_value="1.00",
        final_letter_grade="A",
        final_percentage="90.00",
        gpa_points="4.00",
        provider="Acme Online Academy",
        dual_enrollment_label="Dual Enrollment",
    )

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content
    courses = [row for term in response.json()["terms"] for row in term["courses"]]
    math = next(row for row in courses if row["course_code"] == "MATH-101")
    assert math["provider"] == "Acme Online Academy"
    assert math["dual_enrollment_label"] == "Dual Enrollment"


def test_student_transcript_contract_includes_dual_enrollment_metadata():
    school = School.objects.create(name="Metadata School 2")
    user = _mk_user(school=school, email="director-metadata2@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")
    student = _seed_transcript_test_data(school=school)
    section = Section.objects.get(school_id=school.id, course__code="MATH-101")

    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=section.course,
        term=section.term_ref,
        credit_value="1.00",
        final_letter_grade="A",
        final_percentage="90.00",
        gpa_points="4.00",
        provider="Acme Online Academy",
        dual_enrollment_label="Dual Enrollment",
    )

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        f"/api/v1/academics/students/{student.id}/transcript/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content
    courses = [
        row
        for year in response.json()["school_years"]
        for term in year["terms"]
        for row in term["courses"]
    ]
    math = next(row for row in courses if row["course_code"] == "MATH-101")
    assert math["provider"] == "Acme Online Academy"
    assert math["dual_enrollment_label"] == "Dual Enrollment"
