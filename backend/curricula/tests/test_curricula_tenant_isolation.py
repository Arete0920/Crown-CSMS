"""Tenant isolation and persistent-RBAC tests for governed curricula."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course
from core.models import CrownPermission, RolePermission, School, UserRole
from curricula.governance import create_new_draft
from curricula.models import CurriculumMap, Lesson, Unit

pytestmark = pytest.mark.django_db


def _permission(code):
    permission, _ = CrownPermission.objects.get_or_create(code=code, defaults={"description": code})
    return permission


def _user(school, role_code, permissions):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"curriculum-{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex}@example.test",
        password="pass12345!",
        school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    for code in permissions:
        RolePermission.objects.get_or_create(role_code=role_code, permission=_permission(code))
    return user


def _client(user, school):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _seed_curriculum(school, code, title):
    course = Course.objects.create(school_id=school.id, code=code, name=f"{code} Course")
    curriculum_map = CurriculumMap.objects.create(
        school_id=school.id,
        course=course,
        title=title,
        active=True,
    )
    version = create_new_draft(curriculum_map=curriculum_map)
    unit = Unit.objects.create(
        school_id=school.id,
        curriculum_map=curriculum_map,
        curriculum_version=version,
        sequence=1,
        title="Foundations",
    )
    lesson = Lesson.objects.create(
        school_id=school.id,
        unit=unit,
        sequence=1,
        title="Lesson One",
    )
    return course, curriculum_map, version, unit, lesson


@pytest.fixture
def two_schools():
    school_a = School.objects.create(name="Curriculum School A")
    school_b = School.objects.create(name="Curriculum School B")
    a = _seed_curriculum(school_a, "MATH101", "Math Map")
    b = _seed_curriculum(school_b, "SCI101", "Science Map")
    return school_a, school_b, a, b


def test_view_permission_is_required_and_tenant_scoped(two_schools):
    school_a, _school_b, a, b = two_schools
    _course_a, map_a, version_a, unit_a, lesson_a = a
    _course_b, map_b, _version_b, _unit_b, _lesson_b = b

    allowed = _client(_user(school_a, "TEACHER", ["curriculum.view"]), school_a)
    denied = _client(_user(school_a, "NO_CURRICULUM", []), school_a)

    maps = allowed.get("/api/v1/curricula/maps/")
    versions = allowed.get("/api/v1/curricula/versions/")
    units = allowed.get("/api/v1/curricula/units/")
    lessons = allowed.get("/api/v1/curricula/lessons/")

    assert maps.status_code == 200
    assert [row["curriculum_map_id"] for row in maps.json()] == [str(map_a.id)]
    assert versions.status_code == 200
    assert [row["curriculum_version_id"] for row in versions.json()] == [str(version_a.id)]
    assert units.status_code == 200 and units.json()[0]["unit_id"] == str(unit_a.id)
    assert lessons.status_code == 200 and lessons.json()[0]["lesson_id"] == str(lesson_a.id)
    assert allowed.get(f"/api/v1/curricula/maps/{map_b.id}/").status_code == 404
    assert denied.get("/api/v1/curricula/maps/").status_code == 403


def test_read_only_teacher_cannot_mutate(two_schools):
    school_a, _school_b, a, _b = two_schools
    course_a, map_a, version_a, _unit_a, _lesson_a = a
    client = _client(_user(school_a, "TEACHER", ["curriculum.view"]), school_a)

    assert client.post(
        "/api/v1/curricula/maps/",
        {"course_id": str(course_a.id), "title": "Denied Map"},
        format="json",
    ).status_code == 403
    assert client.patch(
        f"/api/v1/curricula/maps/{map_a.id}/",
        {"title": "Denied"},
        format="json",
    ).status_code == 403
    assert client.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "review"},
        format="json",
    ).status_code == 403


def test_editor_can_author_but_cannot_approve_without_publish_permission(two_schools):
    school_a, _school_b, a, _b = two_schools
    _course_a, _map_a, version_a, _unit_a, _lesson_a = a
    editor = _client(
        _user(school_a, "CURRICULUM_EDITOR", ["curriculum.view", "curriculum.edit"]),
        school_a,
    )

    review = editor.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "review"},
        format="json",
    )
    assert review.status_code == 200
    approve = editor.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "approved"},
        format="json",
    )
    assert approve.status_code == 403


def test_publish_permission_and_segregation_of_duties(two_schools):
    school_a, _school_b, a, _b = two_schools
    _course_a, _map_a, version_a, _unit_a, _lesson_a = a
    submitter = _client(
        _user(school_a, "HEAD_OF_SCHOOL", ["curriculum.view", "curriculum.edit", "curriculum.publish"]),
        school_a,
    )
    approver = _client(
        _user(school_a, "REGISTRAR", ["curriculum.view", "curriculum.edit", "curriculum.publish"]),
        school_a,
    )

    assert submitter.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "review"},
        format="json",
    ).status_code == 200
    assert submitter.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "approved"},
        format="json",
    ).status_code == 400
    assert approver.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "approved"},
        format="json",
    ).status_code == 200
    published = approver.post(
        f"/api/v1/curricula/versions/{version_a.id}/transition/",
        {"status": "published"},
        format="json",
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"


def test_cross_tenant_relations_fail_closed(two_schools):
    school_a, _school_b, a, b = two_schools
    _course_a, map_a, _version_a, _unit_a, _lesson_a = a
    _course_b, _map_b, version_b, _unit_b, _lesson_b = b
    client = _client(
        _user(school_a, "REGISTRAR", ["curriculum.view", "curriculum.edit", "curriculum.publish"]),
        school_a,
    )

    response = client.post(
        "/api/v1/curricula/units/",
        {
            "curriculum_map_id": str(map_a.id),
            "curriculum_version_id": str(version_b.id),
            "sequence": 2,
            "title": "Cross Tenant",
        },
        format="json",
    )
    assert response.status_code == 400


def test_unauthenticated_requests_are_denied():
    client = APIClient()
    assert client.get("/api/v1/curricula/maps/").status_code in (401, 403)
