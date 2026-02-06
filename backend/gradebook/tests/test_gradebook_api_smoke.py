"""
Smoke tests for gradebook API endpoints.

These tests verify the core contracts:
- GET /api/v1/gradebook/sections/ returns paginated results
- GET /api/v1/gradebook/sections/<id>/grades/ returns {section_id, assignments, rows}

They use minimal test data and call_command to keep them close to real demo usage.
"""
import uuid
import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, School, Staff, UserRole
from households.models import Household, Student
from academics.models import Course, Enrollment, Section, Term, TeacherAssignment


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


def _seed_minimal_academics(*, school: School, staff_email: str):
    """Create minimal academic data: 1 year, 1 term, 1 section with 1 enrollment and 1 teacher."""
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
    course = Course.objects.create(
        school_id=school.id,
        code="MATH-101",
        name="Mathematics",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Test Teacher",
    )

    # Create staff record and teacher assignment
    staff = Staff.objects.create(
        school=school,
        first_name="Test",
        last_name="Teacher",
        email=staff_email,
        role_type="TEACHER",
        status="ACTIVE",
    )
    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)

    household = Household.objects.create(school_id=school.id, name="Test Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name="Student",
        grade_level="5",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)

    return section, staff


def test_gradebook_sections_returns_paginated_results():
    """Verify sections endpoint returns paginated API response."""
    school = School.objects.create(name="Test School")
    section, staff = _seed_minimal_academics(school=school, staff_email="teacher@test.local")

    user = _mk_user(school=school, email=staff.email)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/gradebook/sections/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert "results" in data, "Expected paginated response with 'results' key"
    assert "total" in data, "Expected paginated response with 'total' key"
    assert isinstance(data["results"], list)
    assert data["total"] >= 1, "Should have at least one section"


def test_gradebook_grades_returns_assignments_and_rows():
    """Verify grades endpoint returns {section_id, assignments, rows} structure."""
    school = School.objects.create(name="Test School")
    section, staff = _seed_minimal_academics(school=school, staff_email="teacher@test.local")

    # Use seed command to populate grades (smoke test: prove seed + API flow)
    call_command("seed_gradebook_demo", "--school-id", str(school.id))

    user = _mk_user(school=school, email=staff.email)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(
        f"/api/v1/gradebook/sections/{section.id}/grades/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert "section_id" in data
    assert data["section_id"] == str(section.id)
    assert "assignments" in data and isinstance(data["assignments"], list)
    assert "rows" in data and isinstance(data["rows"], list)
    assert len(data["assignments"]) > 0, "Should have assignments from seed command"
    assert len(data["rows"]) > 0, "Should have student rows with grades"
