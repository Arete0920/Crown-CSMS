import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Assignment, AssignmentCategory, Course, Enrollment, Section, TeacherAssignment
from core.models import CrownPermission, RolePermission, School, Staff, UserRole
from gradebook.models import GradeEntry
from households.models import Household, Student


pytestmark = pytest.mark.django_db
GRADEBOOK_EDIT = "gradebook.edit"


def _user(*, school, email, role_code, staff=None):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"gradebook-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
        staff=staff,
    )
    UserRole.objects.create(school=school, user=user, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(
        code=GRADEBOOK_EDIT,
        defaults={"description": "Create or modify grades within authorized sections"},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    return user


def _student(*, school, household, first_name):
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name=first_name,
        last_name="Gradebook",
        grade_level="8",
    )


def _graph(name="Authority"):
    school = School.objects.create(name=f"{name} School")
    course = Course.objects.create(
        school_id=school.id,
        code=f"{name[:4].upper()}-101",
        name="Gradebook Course",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
        teacher_name="Assigned Teacher",
    )
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Assessments",
        weight_percent=100,
        sort_order=1,
        is_active=True,
    )
    assignment = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name="Assessment 1",
        points_possible="100.00",
        is_published=True,
    )
    household = Household.objects.create(
        school_id=school.id,
        name=f"{name} Household",
    )
    enrolled = _student(
        school=school,
        household=household,
        first_name="Enrolled",
    )
    nonmember = _student(
        school=school,
        household=household,
        first_name="Nonmember",
    )
    Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=enrolled,
    )
    return school, section, assignment, enrolled, nonmember


def _teacher(*, school, section, assigned=True):
    staff = Staff.objects.create(
        school=school,
        first_name="Assigned" if assigned else "Unassigned",
        last_name="Teacher",
        email=f"teacher-{uuid.uuid4()}@test.local",
        role_type="TEACHER",
        status="ACTIVE",
    )
    if assigned:
        TeacherAssignment.objects.create(
            school_id=school.id,
            section=section,
            staff=staff,
        )
    return _user(
        school=school,
        email=staff.email,
        role_code="TEACHER",
        staff=staff,
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _upsert_url(section, assignment):
    return (
        f"/api/v1/gradebook/sections/{section.id}/assignments/"
        f"{assignment.id}/grades/upsert/"
    )


def _patch_url(entry):
    return f"/api/v1/gradebook/grade-entries/{entry.id}/"


def test_bulk_upsert_is_idempotent_for_assigned_teacher_and_enrolled_student():
    school, section, assignment, enrolled, _ = _graph()
    teacher = _teacher(school=school, section=section, assigned=True)
    client = _client(teacher)
    payload = {"grades": [{"student_id": str(enrolled.id), "points_earned": "88.50"}]}

    first = client.post(
        _upsert_url(section, assignment),
        payload,
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    second = client.post(
        _upsert_url(section, assignment),
        payload,
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert first.status_code == 200, first.content
    assert first.json()["created"] == 1
    assert second.status_code == 200, second.content
    assert second.json()["updated"] == 1
    assert GradeEntry.objects.filter(
        school_id=school.id,
        section=section,
        student=enrolled,
        assignment=assignment,
    ).count() == 1


def test_bulk_upsert_rejects_nonmember_without_partial_write():
    school, section, assignment, enrolled, nonmember = _graph()
    registrar = _user(
        school=school,
        email="registrar@test.local",
        role_code="REGISTRAR",
    )
    client = _client(registrar)

    response = client.post(
        _upsert_url(section, assignment),
        {
            "grades": [
                {"student_id": str(enrolled.id), "points_earned": 95},
                {"student_id": str(nonmember.id), "points_earned": 90},
            ]
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 400, response.content
    assert GradeEntry.objects.filter(school_id=school.id, section=section).count() == 0


def test_bulk_upsert_rejects_cross_tenant_student_without_write():
    school, section, assignment, _enrolled, _ = _graph("Primary")
    other_school, _other_section, _other_assignment, other_student, _ = _graph("Other")
    registrar = _user(
        school=school,
        email="registrar-cross-tenant@test.local",
        role_code="REGISTRAR",
    )
    client = _client(registrar)

    response = client.post(
        _upsert_url(section, assignment),
        {"grades": [{"student_id": str(other_student.id), "points_earned": 90}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert other_school.id != school.id
    assert response.status_code == 400, response.content
    assert GradeEntry.objects.filter(school_id=school.id, section=section).count() == 0


def test_bulk_upsert_rejects_duplicate_student_rows_without_write():
    school, section, assignment, enrolled, _ = _graph()
    registrar = _user(
        school=school,
        email="registrar-duplicate@test.local",
        role_code="REGISTRAR",
    )
    client = _client(registrar)

    response = client.post(
        _upsert_url(section, assignment),
        {
            "grades": [
                {"student_id": str(enrolled.id), "points_earned": 80},
                {"student_id": str(enrolled.id), "points_earned": 90},
            ]
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 400, response.content
    assert GradeEntry.objects.filter(school_id=school.id, section=section).count() == 0


def test_unassigned_teacher_cannot_mutate_section():
    school, section, assignment, enrolled, _ = _graph()
    teacher = _teacher(school=school, section=section, assigned=False)
    client = _client(teacher)

    response = client.post(
        _upsert_url(section, assignment),
        {"grades": [{"student_id": str(enrolled.id), "points_earned": 90}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 404, response.content
    assert GradeEntry.objects.filter(school_id=school.id, section=section).count() == 0


def test_permission_revocation_is_revalidated_on_each_write():
    school, section, assignment, enrolled, _ = _graph()
    teacher = _teacher(school=school, section=section, assigned=True)
    client = _client(teacher)

    permission = CrownPermission.objects.get(code=GRADEBOOK_EDIT)
    RolePermission.objects.filter(role_code="TEACHER", permission=permission).delete()

    response = client.post(
        _upsert_url(section, assignment),
        {"grades": [{"student_id": str(enrolled.id), "points_earned": 90}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403, response.content
    assert GradeEntry.objects.filter(school_id=school.id, section=section).count() == 0


def test_patch_revalidates_assignment_and_roster_authority():
    school, section, assignment, enrolled, _ = _graph()
    teacher = _teacher(school=school, section=section, assigned=True)
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=enrolled,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=75,
        points_possible=assignment.points_possible,
    )
    client = _client(teacher)

    ok = client.patch(
        _patch_url(entry),
        {"points_earned": 91},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert ok.status_code == 200, ok.content
    entry.refresh_from_db()
    assert entry.points_earned == 91

    Enrollment.objects.filter(section=section, student=enrolled).delete()
    denied = client.patch(
        _patch_url(entry),
        {"points_earned": 92},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert denied.status_code == 400, denied.content
    entry.refresh_from_db()
    assert entry.points_earned == 91


def test_patch_denies_unassigned_teacher_even_for_existing_entry():
    school, section, assignment, enrolled, _ = _graph()
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=enrolled,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=75,
        points_possible=assignment.points_possible,
    )
    teacher = _teacher(school=school, section=section, assigned=False)
    client = _client(teacher)

    response = client.patch(
        _patch_url(entry),
        {"points_earned": 99},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 404, response.content
    entry.refresh_from_db()
    assert entry.points_earned == 75
