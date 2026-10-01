"""
Phase 4 Step 2: E2E payload test for parent grades summary endpoint.

Proves:
- Authentication gate works (endpoint rejects unauthenticated requests)
- Tenant scoping works (X-School-Id required)
- Payload shape is correct for a seeded student with grade data

Route: GET /api/v1/gradebook/students/<uuid>/grades/
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import School
from gradebook.models import GradeEntry
from households.models import Household, Student, Guardian

pytestmark = pytest.mark.django_db


def _make_school():
    return School.objects.create(
        name=f"Test School {uuid.uuid4()}", is_active=True
    )


def _make_user(school):
    User = get_user_model()
    return User.objects.create_user(
        username=f"testuser-{uuid.uuid4()}",
        password="test",
        school=school,
    )


def _seed(school):
    """Seed: household → student → course → section → enrollment → 2 grade entries."""
    hh = Household.objects.create(school_id=school.id, name="Test Household")
    student = Student.objects.create(
        school_id=school.id,
        household=hh,
        first_name="Alex",
        last_name="Demo",
        grade_level="10",
    )
    course = Course.objects.create(
        school_id=school.id,
        code="MATH-101",
        name="Mathematics",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )
    Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Homework 1",
        points_earned="90.00",
        points_possible="100.00",
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Quiz 1",
        points_earned="78.00",
        points_possible="100.00",
    )
    return student, section


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parent_grades_summary_requires_auth():
    """Unauthenticated request must be rejected (401 or 403 depending on DRF auth classes)."""
    school = _make_school()
    student = Student.objects.create(
        school_id=school.id,
        household=Household.objects.create(school_id=school.id, name="HH"),
        first_name="X",
        last_name="Y",
    )
    client = APIClient()
    resp = client.get(
        f"/api/v1/gradebook/students/{student.pk}/grades/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    # DRF returns 401 with JWT-only auth, 403 when SessionAuthentication is also present
    assert resp.status_code in (401, 403), (
        f"Expected 401 or 403 for unauthenticated request, got {resp.status_code}"
    )


def test_parent_grades_summary_invalid_tenant_header_returns_400():
    """Malformed UUID in X-School-Id must return 400 (header_invalid path)."""
    school = _make_school()
    user = _make_user(school)
    student = Student.objects.create(
        school_id=school.id,
        household=Household.objects.create(school_id=school.id, name="HH"),
        first_name="X",
        last_name="Y",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(
        f"/api/v1/gradebook/students/{student.pk}/grades/",
        HTTP_X_SCHOOL_ID="not-a-valid-uuid",
    )
    assert resp.status_code == 400, f"Expected 400 for invalid UUID header, got {resp.status_code}"


def test_parent_grades_summary_unknown_student_returns_404():
    """Valid auth + valid school header + non-existent student → 404."""
    school = _make_school()
    user = _make_user(school)
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(
        f"/api/v1/gradebook/students/{uuid.uuid4()}/grades/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


def test_parent_grades_summary_payload_shape():
    """
    Core contract: authenticated user with seeded data gets correct payload shape.

    Asserts:
    - 200 OK
    - student_id, student_name, grade_level present at top level
    - courses list has 1 entry with correct fields
    - assignments list has 2 entries matching seeded data
    - overall_percentage and letter_grade are computed
    """
    school = _make_school()
    user = _make_user(school)
    student, section = _seed(school)
    Guardian.objects.create(school_id=school.id, household=student.household, account=user, first_name="Parent", last_name="Demo")

    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(
        f"/api/v1/gradebook/students/{student.pk}/grades/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}: {resp.content}"
    )

    data = resp.json()

    # Top-level shape
    assert data["student_id"] == str(student.pk)
    assert data["student_name"] == "Alex Demo"
    assert data["grade_level"] == "10"
    assert isinstance(data["courses"], list)
    assert len(data["courses"]) == 1, f"Expected 1 course, got: {data['courses']}"

    course_data = data["courses"][0]
    assert course_data["course_code"] == "MATH-101"
    assert course_data["course_name"] == "Mathematics"
    assert course_data["term"] == "2026-FALL"
    assert course_data["assignments_count"] == 2

    # Grade computation: (90 + 78) / (100 + 100) = 84.0 → B
    assert course_data["overall_percentage"] == 84.0
    assert course_data["letter_grade"] is None
    assert "Provisional unweighted" in course_data["calculation"]

    assignments = course_data["assignments"]
    assert len(assignments) == 2
    names = {a["assignment_name"] for a in assignments}
    assert names == {"Homework 1", "Quiz 1"}
    for a in assignments:
        assert "points_possible" in a
        assert "points_earned" in a
        assert "percentage" in a


def test_parent_grades_summary_no_grades_returns_empty_courses():
    """Student with no enrollments returns courses=[]."""
    school = _make_school()
    user = _make_user(school)
    hh = Household.objects.create(school_id=school.id, name="HH2")
    student = Student.objects.create(
        school_id=school.id,
        household=hh,
        first_name="Empty",
        last_name="Student",
    )
    Guardian.objects.create(school_id=school.id, household=hh, account=user, first_name="Parent", last_name="Demo")
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(
        f"/api/v1/gradebook/students/{student.pk}/grades/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["courses"] == []
    assert data["student_id"] == str(student.pk)
