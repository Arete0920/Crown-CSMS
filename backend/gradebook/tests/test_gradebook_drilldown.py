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


def test_section_drilldown_returns_shape():
    """
    Drilldown endpoint exists and returns correct shape.
    """
    school = School.objects.create(name="Test School")
    section, _ = _seed_academics_data(school)

    # seed via command (12 assignments with realistic missingness)
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--per-section=12", "--seed=2026")

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    # Call drilldown endpoint
    resp = client.get(
        f"/api/v1/gradebook/sections/{section.id}/drilldown/?bucket=all&limit=25&offset=0",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    data = resp.json()

    # Validate response shape
    assert "section_id" in data
    assert "section_name" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 25
    assert data["offset"] == 0
    assert "rows" in data
    assert isinstance(data["rows"], list)

    # With seeded data, expect rows
    assert len(data["rows"]) > 0

    # Check row shape
    row = data["rows"][0]
    assert "student_id" in row
    assert "student_name" in row
    assert "grade_level" in row
    assert "total_points_earned" in row
    assert "total_points_possible" in row
    assert "pct" in row
    assert "status" in row
    assert "assignments_count" in row
    assert "missing_count" in row
    assert "late_count" in row


def test_section_drilldown_bucket_missing():
    """
    Filter by bucket='missing' returns only students with missing grades.
    """
    school = School.objects.create(name="Test School")
    section, _ = _seed_academics_data(school)
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--per-section=12", "--seed=2026")

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get(
        f"/api/v1/gradebook/sections/{section.id}/drilldown/?bucket=missing&limit=25&offset=0",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    data = resp.json()

    # All returned rows should have missing_count > 0
    for row in data["rows"]:
        assert row["missing_count"] > 0, f"Row {row['student_id']} has no missing grades"
        assert row["status"] == "missing"


def test_section_drilldown_pagination():
    """
    Pagination with limit and offset works correctly.
    """
    school = School.objects.create(name="Test School")
    section, _ = _seed_academics_data(school)
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--per-section=12", "--seed=2026")

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    # First page
    resp1 = client.get(
        f"/api/v1/gradebook/sections/{section.id}/drilldown/?bucket=all&limit=2&offset=0",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1["rows"]) <= 2

    # Second page
    resp2 = client.get(
        f"/api/v1/gradebook/sections/{section.id}/drilldown/?bucket=all&limit=2&offset=2",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["offset"] == 2

    # Total should be consistent
    assert data1["total"] == data2["total"]
