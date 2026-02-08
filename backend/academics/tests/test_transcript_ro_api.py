"""
API tests for Transcript Read-Only endpoint.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from core.models import AcademicYear, School, Staff, UserRole
from academics.models import Course, Enrollment, Section, Term
from households.models import Household, Student
from gradebook.models import GradeEntry

pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str):
    """Create a test user for the school."""
    User = get_user_model()
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )


def _assign_role(*, user, school: School, role_code: str):
    """Assign a role to the user."""
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _seed_transcript_test_data(*, school: School):
    """Create minimal transcript test data: 1 student, 2 terms, 2 sections, grades."""
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
    
    course1 = Course.objects.create(school_id=school.id, code="MATH-101", name="Mathematics")
    course2 = Course.objects.create(school_id=school.id, code="ELA-101", name="English Language Arts")
    
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
    
    # Add grades: MATH-101: 90/100 (A), ELA-101: 80/100 (B)
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
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    client = APIClient()
    client.force_authenticate(user)

    unknown = uuid.uuid4()
    resp = client.get(f"/api/v1/academics/transcript/{unknown}/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 404


def test_transcript_ro_returns_terms_and_courses_for_demo_student():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="director@test.local")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    student = _seed_transcript_test_data(school=school)
    
    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/academics/transcript/{student.id}/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert "student" in data
    assert data["student"]["student_id"] == str(student.id)
    assert data["student"]["first_name"] == "Test"
    assert data["student"]["last_name"] == "Student"
    assert "terms" in data and isinstance(data["terms"], list)
    assert len(data["terms"]) == 2  # 2 terms seeded

    # Contract keys
    t0 = data["terms"][0]
    assert "term_code" in t0
    assert "courses" in t0
    assert len(t0["courses"]) >= 1
    
    # Verify course structure
    c0 = t0["courses"][0]
    assert "section_id" in c0
    assert "course_code" in c0
    assert "course_name" in c0
    assert "teacher_name" in c0
    assert "final_percent" in c0
    assert "final_letter" in c0
    assert "credits" in c0
    
    # Verify GPA fields exist
    assert "term_gpa_mvp" in t0
    assert "cumulative_gpa_mvp" in data
    assert "notes" in data


def test_transcript_ro_alias_returns_same_contract():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="director@test.local")
    _assign_role(user=user, school=school, role_code="DIRECTOR")

    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(
        f"/api/v1/transcripts/students/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert data["student"]["student_id"] == str(student.id)
    assert "terms" in data and isinstance(data["terms"], list)


def test_student_transcript_contract_shape():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="director@test.local")
    _assign_role(user=user, school=school, role_code="DIRECTOR")

    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(
        f"/api/v1/academics/students/{student.id}/transcript/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert data["student_id"] == str(student.id)
    assert "student_name" in data
    assert "school_years" in data and isinstance(data["school_years"], list)
    assert data["school_years"], data
    year0 = data["school_years"][0]
    assert "school_year" in year0
    assert "terms" in year0 and isinstance(year0["terms"], list)
    term0 = year0["terms"][0]
    assert "term_id" in term0
    assert "term_name" in term0
    assert "courses" in term0 and isinstance(term0["courses"], list)
    course0 = term0["courses"][0]
    assert "section_id" in course0
    assert "course_code" in course0
    assert "course_name" in course0
    assert "credits" in course0
    assert "teacher" in course0
    assert "final_grade" in course0
    assert "status" in course0
