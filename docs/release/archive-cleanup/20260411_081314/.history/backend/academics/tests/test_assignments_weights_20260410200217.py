"""
Tests for Assignment/Category models, weighted grading, and CRUD APIs.

Must-have tests (per spec):
1. Weights=0 fallback: transcript final_percent equals earned/possible
2. Weights=100 with data: weighted final matches expected
3. Empty category renormalization: category with no assignments doesn't tank grade
4. Category sum validation: API rejects weights sum not 0 or 100 (when active)
5. Create category + assignment; list endpoints return them
6. Permissions: non-admin cannot POST/PATCH/DELETE
"""
import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Assignment, AssignmentCategory, Course, Enrollment, Section, Term
from academics.transcript_views import _compute_section_final_percent
from core.models import AcademicYear, School, UserRole
from gradebook.models import GradeEntry
from households.models import Household, Student

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


def _seed_base_data(*, school: School):
    """Create academic year, term, course, and section."""
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
        name="Fall 2026",
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code="MATH-101",
        name="Algebra I",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term="2026-FALL",
        teacher_name="Mr. Anderson",
    )
    household = Household.objects.create(
        school_id=school.id,
        name="Test Family",
    )
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name="Student",
        grade_level="9",
    )
    Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )
    return section, student


# ========== Math/Behavior Tests ==========

def test_weights_zero_fallback_uses_simple_sum(transactional_db):
    """
    When category weights sum to 0, final_percent = earned/possible (unweighted).
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    # Create category with weight=0 (unconfigured)
    cat = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=Decimal("0"),
        is_active=True,
    )
    
    # Create assignment (not strictly needed for GradeEntry fallback, but represents real scenario)
    Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=cat,
        name="HW1",
        points_possible=Decimal("100"),
    )
    
    # Create GradeEntry: 85/100
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="HW1",
        points_earned=Decimal("85"),
        points_possible=Decimal("100"),
    )
    
    final = _compute_section_final_percent(str(school.id), section.id, student.id)
    
    assert final == 85.0


def test_weights_configured_uses_weighted_grading(transactional_db):
    """
    When category weights sum to 100, use weighted grading formula.
    
    Example:
    - Tests (50%): 90/100 = 90%
    - Homework (50%): 80/100 = 80%
    - Weighted final = 0.90*0.5 + 0.80*0.5 = 0.85 = 85%
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    # Create two categories with weights summing to 100
    cat_tests = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("50"),
        is_active=True,
    )
    cat_hw = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=Decimal("50"),
        is_active=True,
    )
    
    # Create assignments
    test_asg = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=cat_tests,
        name="Test 1",
        points_possible=Decimal("100"),
    )
    hw_asg = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=cat_hw,
        name="HW1",
        points_possible=Decimal("100"),
    )
    
    # Create grade entries
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Test 1",
        points_earned=Decimal("90"),
        points_possible=Decimal("100"),
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="HW1",
        points_earned=Decimal("80"),
        points_possible=Decimal("100"),
    )
    
    final = _compute_section_final_percent(str(school.id), section.id, student.id)
    
    # Expected: (90/100)*0.5 + (80/100)*0.5 = 0.45 + 0.40 = 0.85 = 85.0%
    assert final == 85.0


def test_empty_category_renormalization(transactional_db):
    """
    When a category has no assignments/points, exclude it and renormalize weights.
    
    Example:
    - Tests (40%): 90/100 = 90%
    - Homework (30%): 80/100 = 80%
    - Projects (30%): 0/0 (no assignments - excluded)
    - Renormalized: Tests = 40/(40+30) = 57.1%, Homework = 30/(40+30) = 42.9%
    - Weighted final = 0.90*0.571 + 0.80*0.429 = 0.514 + 0.343 = 0.857 = 85.7%
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    cat_tests = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("40"),
        is_active=True,
    )
    cat_hw = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=Decimal("30"),
        is_active=True,
    )
    cat_projects = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Projects",
        weight_percent=Decimal("30"),
        is_active=True,
    )
    
    # Create assignments only in Tests and Homework (no Projects)
    Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=cat_tests,
        name="Test 1",
        points_possible=Decimal("100"),
    )
    Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=cat_hw,
        name="HW1",
        points_possible=Decimal("100"),
    )
    
    # Grade entries
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Test 1",
        points_earned=Decimal("90"),
        points_possible=Decimal("100"),
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="HW1",
        points_earned=Decimal("80"),
        points_possible=Decimal("100"),
    )
    
    final = _compute_section_final_percent(str(school.id), section.id, student.id)
    
    # Expected: (90/100)*(40/70) + (80/100)*(30/70) = 0.9*0.571 + 0.8*0.429 = 0.514 + 0.343 = 0.857 = 85.7%
    assert final == 85.7


def test_no_categories_uses_gradeentry_fallback(transactional_db):
    """
    When section has no categories, use simple GradeEntry sum.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    # No categories created
    
    # Create grade entries directly (demo scenario)
    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Random Entry",
        points_earned=Decimal("75"),
        points_possible=Decimal("100"),
    )
    
    final = _compute_section_final_percent(str(school.id), section.id, student.id)
    
    assert final == 75.0


# ========== API Validation Tests ==========

def test_category_weight_validation_rejects_invalid_sum(transactional_db):
    """
    API rejects category creation when active weights don't sum to 0 or 100.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Create first category with 100% weight (valid)
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/categories/",
        {
            "name": "Tests",
            "weight_percent": "100",
            "is_active": True,
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 201
    
    # Try to create second category with any weight (total would be > 100, invalid)
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/categories/",
        {
            "name": "Homework",
            "weight_percent": "30",
            "is_active": True,
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 400
    assert "must sum to 0" in str(resp.data) or "must sum to" in str(resp.data)


def test_assignment_requires_positive_points(transactional_db):
    """
    API rejects assignment creation when points_possible <= 0.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    cat = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("0"),
        is_active=True,
    )
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Try to create assignment with 0 points
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/assignments/",
        {
            "name": "Test 1",
            "category_id": str(cat.id),
            "points_possible": "0",
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 400
    error_msg = str(resp.data)
    assert "must be greater than 0" in error_msg or "greater than" in error_msg


# ========== API CRUD Tests ==========

def test_category_batch_weights_persists_updates(transactional_db):
    """
    Batch weight updates persist to the database and come back in the response.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)

    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")

    cat_tests = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("0"),
        is_active=True,
        sort_order=1,
    )
    cat_hw = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=Decimal("0"),
        is_active=True,
        sort_order=2,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.put(
        f"/api/v1/academics/sections/{section.id}/categories/weights/",
        [
            {"id": str(cat_tests.id), "weight_percent": "40", "is_active": True},
            {"id": str(cat_hw.id), "weight_percent": "60", "is_active": True},
        ],
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 200, resp.data

    cat_tests.refresh_from_db()
    cat_hw.refresh_from_db()

    assert cat_tests.weight_percent == Decimal("40")
    assert cat_hw.weight_percent == Decimal("60")
    assert resp.data["categories"][0]["weight_percent"] == "40.00"
    assert resp.data["categories"][1]["weight_percent"] == "60.00"


def test_category_list_create_and_retrieve(transactional_db):
    """
    Create category via POST, then retrieve via GET.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Create category
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/categories/",
        {
            "name": "Tests",
            "weight_percent": "0",
            "is_active": True,
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 201
    assert resp.data["name"] == "Tests"
    
    category_id = resp.data["id"]
    
    # List categories
    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/categories/",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 200
    assert len(resp.data["categories"]) == 1
    assert resp.data["categories"][0]["name"] == "Tests"


def test_assignment_list_create_and_retrieve(transactional_db):
    """
    Create assignment via POST, then retrieve via GET.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    cat = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("0"),
        is_active=True,
    )
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Create assignment
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/assignments/",
        {
            "name": "Test 1",
            "category_id": str(cat.id),
            "points_possible": "100",
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 201
    assert resp.data["name"] == "Test 1"
    assert resp.data["points_possible"] == "100.00"
    
    # List assignments
    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/assignments/",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 200
    assert len(resp.data["assignments"]) == 1
    assert resp.data["assignments"][0]["name"] == "Test 1"


def test_non_admin_cannot_create_category(transactional_db):
    """
    User without ADMIN or DIRECTOR role cannot POST category.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="teacher@test.com")
    _assign_role(user=user, school=school, role_code="TEACHER")
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/categories/",
        {
            "name": "Tests",
            "weight_percent": "0",
            "is_active": True,
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 403


def test_non_admin_cannot_create_assignment(transactional_db):
    """
    User without ADMIN or DIRECTOR role cannot POST assignment.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="teacher@test.com")
    _assign_role(user=user, school=school, role_code="TEACHER")
    
    cat = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("0"),
        is_active=True,
    )
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    resp = client.post(
        f"/api/v1/academics/sections/{section.id}/assignments/",
        {
            "name": "Test 1",
            "category_id": str(cat.id),
            "points_possible": "100",
        },
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 403


def test_category_update_and_delete(transactional_db):
    """
    PATCH updates category, DELETE removes it.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    cat = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("0"),
        is_active=True,
    )
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Update name
    resp = client.patch(
        f"/api/v1/academics/categories/{cat.id}/",
        {"name": "Exams"},
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 200
    assert resp.data["name"] == "Exams"
    
    # Delete
    resp = client.delete(
        f"/api/v1/academics/categories/{cat.id}/",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 204
    assert not AssignmentCategory.objects.filter(pk=cat.id).exists()


def test_assignment_update_and_delete(transactional_db):
    """
    PATCH updates assignment, DELETE removes it.
    """
    school = School.objects.create(name="Test School")
    section, student = _seed_base_data(school=school)
    
    user = _mk_user(school=school, email="director@test.com")
    _assign_role(user=user, school=school, role_code="DIRECTOR")
    
    cat = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=Decimal("0"),
        is_active=True,
    )
    
    asg = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=cat,
        name="Test 1",
        points_possible=Decimal("100"),
    )
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Update points
    resp = client.patch(
        f"/api/v1/academics/assignments/{asg.id}/",
        {"points_possible": "150"},
        format="json",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 200
    assert resp.data["points_possible"] == "150.00"
    
    # Delete
    resp = client.delete(
        f"/api/v1/academics/assignments/{asg.id}/",
        headers={"X-School-Id": str(school.id)},
    )
    assert resp.status_code == 204
    assert not Assignment.objects.filter(pk=asg.id).exists()
