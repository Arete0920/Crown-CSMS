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


def test_section_summary_returns_counts_and_avg():
    school = School.objects.create(name="Test School")
    _seed_academics_data(school)

    # seed via command (12 assignments with realistic missingness)
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--per-section=12", "--seed=2026")

    user = _mk_user(school=school, email="test@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    # pick a section that has grade entries
    from gradebook.models import GradeEntry
    section_id = GradeEntry.objects.filter(school_id=school.id).values_list("section_id", flat=True).first()
    assert section_id

    resp = client.get(f"/api/v1/gradebook/sections/{section_id}/summary/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200

    data = resp.json()
    assert data["section_id"] == str(section_id)
    assert data["student_count"] > 0
    assert data["assignment_count"] == 12
    assert data["missing_count"] >= 0
    # avg can be None only if possible == 0; in our seed it should exist
    assert data["class_average_pct"] is not None


def test_section_summary_has_all_required_fields():
    """Verify summary returns all required fields with correct types."""
    school = School.objects.create(name="Test School 2")
    _seed_academics_data(school)
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--per-section=12", "--seed=2026")

    user = _mk_user(school=school, email="admin@example.com")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)

    from gradebook.models import GradeEntry
    section_id = GradeEntry.objects.filter(school_id=school.id).values_list("section_id", flat=True).first()
    assert section_id

    resp = client.get(f"/api/v1/gradebook/sections/{section_id}/summary/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200

    data = resp.json()
    # Verify all required fields exist and have correct types
    assert isinstance(data["section_id"], str)
    assert isinstance(data["student_count"], int)
    assert isinstance(data["assignment_count"], int)
    assert isinstance(data["missing_count"], int)
    assert data["class_average_pct"] is None or isinstance(data["class_average_pct"], (int, float))
    assert data["last_updated"] is None or isinstance(data["last_updated"], str)
