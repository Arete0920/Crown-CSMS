import pytest
from rest_framework.test import APIClient
from django.core.management import call_command
import uuid
from django.contrib.auth import get_user_model

from core.models import School, UserRole, AcademicYear, Staff
from households.models import Household, Student
from academics.models import Course, Enrollment, Section, Term


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


def _seed_academics_data(school: School):
    """Create minimal academics data with sections and enrollments."""
    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name="2026-2027",
        defaults={
            "start_date": "2026-08-15",
            "end_date": "2027-06-10",
            "is_current": True,
        },
    )
    term, _ = Term.objects.get_or_create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        defaults={
            "name": "Fall 2026",
            "active": True,
        },
    )
    course, _ = Course.objects.get_or_create(
        school_id=school.id,
        code="MATH-101",
        defaults={"name": "Math"},
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher A",
    )

    # Create students and enrollments
    household = Household.objects.create(school_id=school.id, name="Household A")
    students = []
    for i in range(3):
        student = Student.objects.create(
            school_id=school.id,
            household=household,
            first_name=f"Student{i}",
            last_name=f"LastName{i}",
            grade_level="5",
        )
        students.append(student)
        Enrollment.objects.create(school_id=school.id, section=section, student=student)

    return section, students


def test_section_roster_returns_shape():
    """
    Roster endpoint exists and returns correct response shape.
    """
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    # Call roster endpoint
    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/roster/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    data = resp.json()

    # Validate response shape
    assert "section_id" in data
    assert "section_name" in data
    assert "course_code" in data
    assert "term" in data
    assert "teacher" in data
    assert "students" in data
    assert "counts" in data

    # Validate counts
    assert data["counts"]["students"] == 3
    assert len(data["students"]) == 3


def test_section_roster_deterministic_order():
    """
    Students are ordered deterministically: last_name, first_name, student_id.
    """
    school = School.objects.create(name="Test School")
    section, _ = _seed_academics_data(school)

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/roster/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    data = resp.json()

    # Check ordering (StudentX with LastNameX pattern)
    rows = data["students"]
    assert len(rows) == 3
    # Should be ordered: LastName0, LastName1, LastName2
    assert rows[0]["name"] == "LastName0, Student0"
    assert rows[1]["name"] == "LastName1, Student1"
    assert rows[2]["name"] == "LastName2, Student2"


def test_section_roster_enrollment_status():
    """
    Each student has enrollment_status field.
    """
    school = School.objects.create(name="Test School")
    section, _ = _seed_academics_data(school)

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/roster/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    data = resp.json()

    # All students should have enrollment_status
    for student in data["students"]:
        assert "enrollment_status" in student
        assert student["enrollment_status"] == "active"
