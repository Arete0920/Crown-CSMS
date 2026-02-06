"""
Tenant isolation tests for curricula API.
Verify that users can only access curriculum data for their own school.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from core.models import School
from academics.models import Course
from curricula.models import CurriculumMap, Unit, Lesson


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    """Create a user and associate with a school."""
    User = get_user_model()
    u = User.objects.create_user(
        username=f"user-{uuid.uuid4().hex[:8]}",
        password="pass12345!",
    )
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


@pytest.fixture
def two_schools_with_curricula():
    """Create two schools each with courses, maps, units, and lessons."""
    # School A
    school_a = School.objects.create(name="School A")
    course_a = Course.objects.create(
        school_id=school_a.id,
        code="MATH101",
        name="Mathematics 101",
    )
    map_a = CurriculumMap.objects.create(
        school_id=school_a.id,
        course=course_a,
        title="Math Curriculum Map A",
        active=True,
    )
    unit_a = Unit.objects.create(
        school_id=school_a.id,
        curriculum_map=map_a,
        sequence=1,
        title="Algebra Fundamentals",
    )
    lesson_a = Lesson.objects.create(
        school_id=school_a.id,
        unit=unit_a,
        sequence=1,
        title="Introduction to Variables",
    )

    # School B
    school_b = School.objects.create(name="School B")
    course_b = Course.objects.create(
        school_id=school_b.id,
        code="SCI101",
        name="Science 101",
    )
    map_b = CurriculumMap.objects.create(
        school_id=school_b.id,
        course=course_b,
        title="Science Curriculum Map B",
        active=True,
    )
    unit_b = Unit.objects.create(
        school_id=school_b.id,
        curriculum_map=map_b,
        sequence=1,
        title="Physics Basics",
    )
    lesson_b = Lesson.objects.create(
        school_id=school_b.id,
        unit=unit_b,
        sequence=1,
        title="Newton's Laws",
    )

    return {
        "school_a": school_a,
        "course_a": course_a,
        "map_a": map_a,
        "unit_a": unit_a,
        "lesson_a": lesson_a,
        "school_b": school_b,
        "course_b": course_b,
        "map_b": map_b,
        "unit_b": unit_b,
        "lesson_b": lesson_b,
    }


def test_curriculum_maps_tenant_isolation(two_schools_with_curricula):
    """Verify users only see curriculum maps for their school."""
    data = two_schools_with_curricula
    user_a = _mk_user_with_school(data["school_a"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    # User A should see only school A's maps
    resp = client.get("/api/v1/curricula/maps/")
    assert resp.status_code == 200
    maps = resp.json()
    assert len(maps) == 1
    assert maps[0]["curriculum_map_id"] == str(data["map_a"].id)
    assert maps[0]["course_code"] == "MATH101"


def test_units_tenant_isolation(two_schools_with_curricula):
    """Verify users only see units for their school."""
    data = two_schools_with_curricula
    user_b = _mk_user_with_school(data["school_b"])

    client = APIClient()
    client.force_authenticate(user=user_b)

    # User B should see only school B's units
    resp = client.get("/api/v1/curricula/units/")
    assert resp.status_code == 200
    units = resp.json()
    assert len(units) == 1
    assert units[0]["unit_id"] == str(data["unit_b"].id)
    assert units[0]["title"] == "Physics Basics"


def test_lessons_tenant_isolation(two_schools_with_curricula):
    """Verify users only see lessons for their school."""
    data = two_schools_with_curricula
    user_a = _mk_user_with_school(data["school_a"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    # User A should see only school A's lessons
    resp = client.get("/api/v1/curricula/lessons/")
    assert resp.status_code == 200
    lessons = resp.json()
    assert len(lessons) == 1
    assert lessons[0]["lesson_id"] == str(data["lesson_a"].id)
    assert lessons[0]["title"] == "Introduction to Variables"


def test_curriculum_filter_by_course(two_schools_with_curricula):
    """Verify filtering by course respects tenant isolation."""
    data = two_schools_with_curricula
    user_a = _mk_user_with_school(data["school_a"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    # Filter by school A's course - should work
    resp = client.get(f"/api/v1/curricula/maps/?course_id={data['course_a'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Try to filter by school B's course - should see nothing (tenant boundary)
    resp = client.get(f"/api/v1/curricula/maps/?course_id={data['course_b'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_unit_filter_by_curriculum_map(two_schools_with_curricula):
    """Verify filtering by curriculum map respects tenant isolation."""
    data = two_schools_with_curricula
    user_b = _mk_user_with_school(data["school_b"])

    client = APIClient()
    client.force_authenticate(user=user_b)

    # Filter by school B's map - should work
    resp = client.get(f"/api/v1/curricula/units/?curriculum_map_id={data['map_b'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Try to filter by school A's map - should see nothing
    resp = client.get(f"/api/v1/curricula/units/?curriculum_map_id={data['map_a'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_lesson_filter_by_unit(two_schools_with_curricula):
    """Verify filtering by unit respects tenant isolation."""
    data = two_schools_with_curricula
    user_a = _mk_user_with_school(data["school_a"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    # Filter by school A's unit - should work
    resp = client.get(f"/api/v1/curricula/lessons/?unit_id={data['unit_a'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Try to filter by school B's unit - should see nothing
    resp = client.get(f"/api/v1/curricula/lessons/?unit_id={data['unit_b'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_read_only_endpoints_reject_writes(two_schools_with_curricula):
    """Verify that curriculum endpoints are read-only (reject POST/PUT/PATCH/DELETE)."""
    data = two_schools_with_curricula
    user_a = _mk_user_with_school(data["school_a"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    # Try to POST a new curriculum map - should be rejected
    resp = client.post(
        "/api/v1/curricula/maps/",
        data={
            "course_id": str(data["course_a"].id),
            "title": "New Map",
            "description": "Should fail",
        },
        format="json",
    )
    assert resp.status_code == 405  # Method Not Allowed

    # Try to PUT/update existing map - should be rejected
    resp = client.put(
        f"/api/v1/curricula/maps/{data['map_a'].id}/",
        data={"title": "Updated Title"},
        format="json",
    )
    assert resp.status_code == 405

    # Try to PATCH existing map - should be rejected
    resp = client.patch(
        f"/api/v1/curricula/maps/{data['map_a'].id}/",
        data={"title": "Patched Title"},
        format="json",
    )
    assert resp.status_code == 405

    # Try to DELETE existing map - should be rejected
    resp = client.delete(f"/api/v1/curricula/maps/{data['map_a'].id}/")
    assert resp.status_code == 405


def test_unauthenticated_requests_blocked(two_schools_with_curricula):
    """Verify that unauthenticated users cannot access curricula endpoints."""
    client = APIClient()

    # No authentication - should return 401 or 403
    resp = client.get("/api/v1/curricula/maps/")
    assert resp.status_code in [401, 403]  # Unauthorized or Forbidden

    resp = client.get("/api/v1/curricula/units/")
    assert resp.status_code in [401, 403]

    resp = client.get("/api/v1/curricula/lessons/")
    assert resp.status_code in [401, 403]


def test_curricula_detail_views_tenant_isolation(two_schools_with_curricula):
    """Verify detail endpoints respect tenant boundaries."""
    data = two_schools_with_curricula
    user_a = _mk_user_with_school(data["school_a"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    # User A can access their own map detail
    resp = client.get(f"/api/v1/curricula/maps/{data['map_a'].id}/")
    assert resp.status_code == 200
    assert resp.json()["curriculum_map_id"] == str(data["map_a"].id)

    # User A CANNOT access school B's map detail (should return empty or 404)
    # Note: DRF ReadOnlyModelViewSet may return 404 if queryset filters it out
    resp = client.get(f"/api/v1/curricula/maps/{data['map_b'].id}/")
    assert resp.status_code == 404
