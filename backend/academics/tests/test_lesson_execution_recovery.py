from __future__ import annotations

import pytest

from academics.lesson_execution_models import LessonPlanLesson
from academics.tests.test_lesson_plans import (
    _assign_role,
    _client_auth,
    _mk_school,
    _mk_user,
    _seed_lesson,
    _seed_section,
)
from core.models import CrownPermission, RolePermission

pytestmark = pytest.mark.django_db


def _grant(role_code: str, permission_code: str):
    permission, _ = CrownPermission.objects.get_or_create(
        code=permission_code,
        defaults={"description": permission_code},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _create_plan_with_link():
    school = _mk_school("Recovered Lesson Execution")
    teacher = _mk_user(school=school, email="lesson-execution-teacher@example.org")
    _assign_role(user=teacher, school=school, role_code="TEACHER")
    _grant("TEACHER", "academics.edit")
    section = _seed_section(school)
    section.teacher = teacher
    section.save(update_fields=["teacher", "updated_at"])
    lesson = _seed_lesson(school, section)
    client = _client_auth(teacher, school)

    response = client.post(
        f"/api/academics/sections/{section.id}/lesson-plans/",
        {
            "plan_date": "2026-11-20",
            "lesson_ids": [str(lesson.id)],
            "teacher_notes_private": "Execution-sensitive note",
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    link = LessonPlanLesson.objects.get(lesson_plan_id=response.data["plan_id"], lesson_id=lesson.id)
    return school, teacher, section, lesson, response.data["plan_id"], link, client


def test_plan_write_synchronizes_relational_execution_link():
    school, _teacher, _section, lesson, plan_id, link, _client = _create_plan_with_link()
    assert str(link.school_id) == str(school.id)
    assert str(link.lesson_plan_id) == str(plan_id)
    assert str(link.lesson_id) == str(lesson.id)
    assert link.sequence_order == 1
    assert link.delivery_status == LessonPlanLesson.DeliveryStatus.PLANNED


def test_assigned_teacher_with_persistent_academic_edit_can_record_execution():
    _school, _teacher, _section, _lesson, _plan_id, link, client = _create_plan_with_link()
    response = client.patch(
        f"/api/academics/lesson-plan-execution/{link.id}/",
        {
            "delivery_status": "taught",
            "actual_minutes": 42,
            "actual_started_at": "2026-11-20T14:00:00Z",
            "actual_completed_at": "2026-11-20T14:42:00Z",
            "completion_notes": "Completed as planned.",
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    link.refresh_from_db()
    assert link.delivery_status == LessonPlanLesson.DeliveryStatus.TAUGHT
    assert link.actual_minutes == 42


def test_execution_write_revalidates_section_assignment():
    school, teacher, section, _lesson, _plan_id, link, client = _create_plan_with_link()
    section.teacher = None
    section.save(update_fields=["teacher", "updated_at"])
    response = client.patch(
        f"/api/academics/lesson-plan-execution/{link.id}/",
        {"delivery_status": "partial", "actual_minutes": 20},
        format="json",
    )
    assert response.status_code == 403
    link.refresh_from_db()
    assert link.delivery_status == LessonPlanLesson.DeliveryStatus.PLANNED


def test_academic_edit_without_section_or_broad_authority_is_denied():
    school, _teacher, _section, _lesson, _plan_id, link, _client = _create_plan_with_link()
    outsider = _mk_user(school=school, email="lesson-execution-outsider@example.org")
    _assign_role(user=outsider, school=school, role_code="ACADEMIC_EDITOR_UNSCOPED")
    _grant("ACADEMIC_EDITOR_UNSCOPED", "academics.edit")
    client = _client_auth(outsider, school)
    assert client.get(f"/api/academics/lesson-plan-execution/{link.id}/").status_code == 403


def test_recorded_execution_cannot_be_removed_from_plan():
    _school, _teacher, _section, _lesson, plan_id, link, client = _create_plan_with_link()
    recorded = client.patch(
        f"/api/academics/lesson-plan-execution/{link.id}/",
        {"delivery_status": "partial", "actual_minutes": 20},
        format="json",
    )
    assert recorded.status_code == 200, recorded.data

    removal = client.patch(
        f"/api/academics/lesson-plans/{plan_id}/",
        {"lesson_ids": []},
        format="json",
    )
    assert removal.status_code == 400
    assert LessonPlanLesson.objects.filter(pk=link.pk).exists()


def test_execution_history_cannot_be_cleared_or_reverted():
    _school, _teacher, _section, _lesson, _plan_id, link, client = _create_plan_with_link()
    recorded = client.patch(
        f"/api/academics/lesson-plan-execution/{link.id}/",
        {"delivery_status": "taught", "actual_minutes": 40, "completion_notes": "Taught."},
        format="json",
    )
    assert recorded.status_code == 200, recorded.data

    clear = client.patch(
        f"/api/academics/lesson-plan-execution/{link.id}/",
        {"actual_minutes": None},
        format="json",
    )
    assert clear.status_code == 400
    revert = client.patch(
        f"/api/academics/lesson-plan-execution/{link.id}/",
        {"delivery_status": "planned"},
        format="json",
    )
    assert revert.status_code == 400


def test_cross_tenant_execution_record_is_not_disclosed():
    _school_a, _teacher, _section, _lesson, _plan_id, link, _client = _create_plan_with_link()
    school_b = _mk_school("Recovered Lesson Execution B")
    user_b = _mk_user(school=school_b, email="lesson-execution-b@example.org")
    _assign_role(user=user_b, school=school_b, role_code="TEACHER_B")
    _grant("TEACHER_B", "academics.edit")
    client_b = _client_auth(user_b, school_b)
    assert client_b.get(f"/api/academics/lesson-plan-execution/{link.id}/").status_code == 404
