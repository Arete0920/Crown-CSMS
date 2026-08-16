import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import (
    Assignment,
    AssignmentCategory,
    Course,
    Enrollment,
    Section,
    Term,
    TranscriptEntry,
)
from core.models import AcademicYear, School, UserRole
from gradebook.models import GradeEntry
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _registrar_client(school):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"registrar-{uuid.uuid4()}",
        email=f"registrar-{uuid.uuid4()}@test.local",
        password="test-pass",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="REGISTRAR")
    client = APIClient()
    client.force_authenticate(user)
    return client


def _base_school():
    school = School.objects.create(name="Transcript Test School")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    household = Household.objects.create(school_id=school.id, name="Transcript Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name="Student",
        grade_level="9",
    )
    return school, year, student


def _section(*, school, year, student, code, term_code, term_name, ordering, credits="1.00"):
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code=term_code,
        name=term_name,
        school_year=year.name,
        ordering=ordering,
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code=code,
        name=f"Course {code}",
        credits=credits,
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    return term, course, section


def _ro(client, school, student):
    return client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


def _contract(client, school, student):
    return client.get(
        f"/api/v1/academics/students/{student.id}/transcript/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


def test_unknown_student_is_concealed():
    school, _year, _student = _base_school()
    client = _registrar_client(school)
    response = client.get(
        f"/api/v1/academics/transcript/{uuid.uuid4()}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 404


def test_finalized_transcript_entry_is_authoritative_for_grade_credit_and_gpa():
    school, year, student = _base_school()
    term, course, section = _section(
        school=school,
        year=year,
        student=student,
        code="MATH-101",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
        credits="0.50",
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Current Work",
        points_earned=50,
        points_possible=100,
    )
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course,
        term=term,
        credit_value="1.00",
        final_letter_grade="A",
        final_percentage="95.00",
        gpa_points="4.00",
        provider="Acme Online Academy",
        dual_enrollment_label="Dual Enrollment",
    )

    response = _ro(_registrar_client(school), school, student)
    assert response.status_code == 200, response.content
    data = response.json()
    row = data["terms"][0]["courses"][0]

    assert row["final_percent"] == 95.0
    assert row["final_letter"] == "A"
    assert row["credits"] == "1.00"
    assert row["earned_credits"] == "1.00"
    assert row["gpa_points"] == "4.00"
    assert row["gpa_included"] is True
    assert row["record_status"] == "final"
    assert row["provider"] == "Acme Online Academy"
    assert row["dual_enrollment_label"] == "Dual Enrollment"
    assert data["cumulative_gpa"] == "4.00"


def test_cumulative_and_term_gpa_are_credit_weighted_across_finalized_rows():
    school, year, student = _base_school()
    term1, course1, _section1 = _section(
        school=school,
        year=year,
        student=student,
        code="MATH-101",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
        credits="0.50",
    )
    term2, course2, _section2 = _section(
        school=school,
        year=year,
        student=student,
        code="ELA-101",
        term_code="SPRING",
        term_name="Spring",
        ordering=2,
        credits="1.00",
    )
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course1,
        term=term1,
        credit_value="0.50",
        final_letter_grade="A",
        final_percentage="94.00",
        gpa_points="4.00",
    )
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course2,
        term=term2,
        credit_value="1.00",
        final_letter_grade="B",
        final_percentage="84.00",
        gpa_points="3.00",
    )

    data = _ro(_registrar_client(school), school, student).json()
    assert data["cumulative_gpa"] == "3.33"
    assert data["attempted_credits"] == "1.50"
    assert data["earned_credits"] == "1.50"
    assert [term["term_gpa"] for term in data["terms"]] == ["4.00", "3.00"]


def test_failed_final_course_counts_attempted_credit_but_not_earned_credit():
    school, year, student = _base_school()
    term, course, _section_obj = _section(
        school=school,
        year=year,
        student=student,
        code="SCI-101",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
        credits="1.00",
    )
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course,
        term=term,
        credit_value="1.00",
        final_letter_grade="F",
        final_percentage="55.00",
        gpa_points="0.00",
    )

    data = _ro(_registrar_client(school), school, student).json()
    assert data["attempted_credits"] == "1.00"
    assert data["earned_credits"] == "0.00"
    assert data["cumulative_gpa"] == "0.00"


def test_in_progress_grade_uses_gradebook_and_course_credit_but_not_official_gpa_totals():
    school, year, student = _base_school()
    _term, _course, section = _section(
        school=school,
        year=year,
        student=student,
        code="HIST-101",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
        credits="0.50",
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Exam",
        points_earned=85,
        points_possible=100,
    )

    data = _ro(_registrar_client(school), school, student).json()
    row = data["terms"][0]["courses"][0]
    assert row["record_status"] == "in_progress"
    assert row["final_percent"] == 85.0
    assert row["final_letter"] == "B"
    assert row["credits"] == "0.50"
    assert row["attempted_credits"] == "0.00"
    assert row["earned_credits"] == "0.00"
    assert row["gpa_included"] is False
    assert data["cumulative_gpa"] is None


def test_weighted_gradebook_fallback_is_used_for_in_progress_row():
    school, year, student = _base_school()
    _term, _course, section = _section(
        school=school,
        year=year,
        student=student,
        code="SCI-201",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
    )
    quizzes = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Quizzes",
        weight_percent="40.00",
        sort_order=1,
        is_active=True,
    )
    exams = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Exams",
        weight_percent="60.00",
        sort_order=2,
        is_active=True,
    )
    quiz = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=quizzes,
        name="Quiz",
        points_possible="100.00",
        is_published=True,
    )
    exam = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=exams,
        name="Exam",
        points_possible="100.00",
        is_published=True,
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment=quiz,
        assignment_name=quiz.name,
        points_earned=100,
        points_possible=100,
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment=exam,
        assignment_name=exam.name,
        points_earned=50,
        points_possible=100,
    )

    row = _ro(_registrar_client(school), school, student).json()["terms"][0]["courses"][0]
    assert row["final_percent"] == 70.0
    assert row["final_letter"] == "C"
    assert row["record_status"] == "in_progress"


def test_no_grade_row_remains_in_progress_without_invented_grade():
    school, year, student = _base_school()
    _section(
        school=school,
        year=year,
        student=student,
        code="ART-101",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
        credits="0.25",
    )
    row = _ro(_registrar_client(school), school, student).json()["terms"][0]["courses"][0]
    assert row["record_status"] == "in_progress"
    assert row["final_percent"] is None
    assert row["final_letter"] is None
    assert row["credits"] == "0.25"


def test_both_transcript_contracts_share_authoritative_grade_and_credit_values():
    school, year, student = _base_school()
    term, course, _section_obj = _section(
        school=school,
        year=year,
        student=student,
        code="MATH-301",
        term_code="FALL",
        term_name="Fall",
        ordering=1,
        credits="0.50",
    )
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course,
        term=term,
        credit_value="0.75",
        final_letter_grade="A",
        final_percentage="97.00",
        gpa_points="4.00",
        provider="Partner College",
        dual_enrollment_label="Dual Enrollment",
    )
    client = _registrar_client(school)

    ro = _ro(client, school, student).json()
    contract = _contract(client, school, student).json()
    ro_row = ro["terms"][0]["courses"][0]
    contract_row = contract["school_years"][0]["terms"][0]["courses"][0]

    assert "term_gpa_mvp" not in ro["terms"][0]
    assert "cumulative_gpa_mvp" not in ro
    assert ro["cumulative_gpa"] == contract["cumulative_gpa"] == "4.00"
    assert ro_row["credits"] == contract_row["credits"] == "0.75"
    assert ro_row["final_letter"] == contract_row["final_grade"] == "A"
    assert ro_row["final_percent"] == contract_row["final_percent"] == 97.0
    assert ro_row["provider"] == contract_row["provider"] == "Partner College"
    assert ro_row["dual_enrollment_label"] == contract_row["dual_enrollment_label"] == "Dual Enrollment"
