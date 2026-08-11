from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import AcademicYear, Course, Lesson, LessonResource, Section, Term, Unit
from core.models import School, UserRole

pytestmark = pytest.mark.django_db
User = get_user_model()


def make_school(name: str) -> School:
    return School.objects.create(name=name)


def make_user(*, school: School, email: str):
    return User.objects.create_user(
        username=f"resource-teacher-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )


def assign_role(*, user, school: School, role_code: str) -> None:
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def make_section(*, school: School, code: str, teacher=None) -> Section:
    year = AcademicYear.objects.create(
        school=school,
        name=f"2026-2027-{code}",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=False,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code=f"FALL-{code}",
        name=f"Fall {code}",
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code=code,
        name=f"Course {code}",
    )
    return Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
        teacher=teacher,
    )


def make_lesson(*, school: School, section: Section) -> Lesson:
    unit = Unit.objects.create(
        school_id=school.id,
        course=section.course,
        title=f"Unit {section.course.code}",
        sequence_order=1,
    )
    return Lesson.objects.create(
        school_id=school.id,
        unit=unit,
        title=f"Lesson {section.course.code}",
    )


def client_for(user, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def test_assigned_teacher_can_create_and_reopen_lesson_resource():
    school = make_school("Teacher Resource School")
    teacher = make_user(school=school, email="assigned-resource-teacher@example.org")
    assign_role(user=teacher, school=school, role_code="TEACHER")
    section = make_section(school=school, code="ENG-501", teacher=teacher)
    lesson = make_lesson(school=school, section=section)

    client = client_for(teacher, school)
    created = client.post(
        f"/api/academics/lessons/{lesson.id}/resources/",
        {
            "title": "BJU Press Grade 5 English resource",
            "kind": "link",
            "url": "https://example.org/heritage/english-resource",
        },
        format="json",
    )

    assert created.status_code == 201, created.data
    resource_id = created.data["resource_id"]
    assert created.data["title"] == "BJU Press Grade 5 English resource"

    reopened = client.get(f"/api/academics/lessons/{lesson.id}/resources/")
    assert reopened.status_code == 200
    assert any(str(row["resource_id"]) == str(resource_id) for row in reopened.data)
    assert LessonResource.objects.filter(id=resource_id, school_id=school.id, lesson=lesson).exists()


def test_unassigned_teacher_cannot_create_resource_for_other_course():
    school = make_school("Teacher Resource Isolation School")
    teacher = make_user(school=school, email="isolated-resource-teacher@example.org")
    assign_role(user=teacher, school=school, role_code="TEACHER")

    assigned_section = make_section(school=school, code="ENG-601", teacher=teacher)
    other_section = make_section(school=school, code="SCI-601")
    assert assigned_section.course_id != other_section.course_id
    other_lesson = make_lesson(school=school, section=other_section)

    client = client_for(teacher, school)
    denied = client.post(
        f"/api/academics/lessons/{other_lesson.id}/resources/",
        {"title": "Out-of-scope resource", "kind": "link"},
        format="json",
    )

    assert denied.status_code == 403
    assert not LessonResource.objects.filter(lesson=other_lesson).exists()
