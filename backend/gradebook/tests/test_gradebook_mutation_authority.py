import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Assignment, AssignmentCategory, Course, Enrollment, Section, TeacherAssignment
from core.models import School, Staff, UserRole
from gradebook.models import GradeEntry
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _user(*, school, role_code, email, staff=None):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"gradebook-{uuid.uuid4()}",
        email=email,
        password="TestPass!1",
        school=school,
    )
    if staff is not None:
        user.staff = staff
        user.save(update_fields=["staff"])
    UserRole.objects.create(school=school, user=user, role_code=role_code)
    return user


def _graph():
    school = School.objects.create(name="Gradebook Mutation School")
    course = Course.objects.create(school_id=school.id, code="GB-101", name="Gradebook Course")
    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL")
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=100,
        sort_order=1,
        is_active=True,
    )
    assignment = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name="Exam",
        points_possible="100.00",
        is_published=True,
    )
    household = Household.objects.create(school_id=school.id, name="Household")
    enrolled = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Enrolled",
        last_name="Student",
        grade_level="9",
    )
    nonmember = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Nonmember",
        last_name="Student",
        grade_level="9",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=enrolled)
    staff = Staff.objects.create(
        school=school,
        first_name="Assigned",
        last_name="Teacher",
        email="assigned.teacher@gradebook.test",
        role_type="TEACHER",
        status="ACTIVE",
    )
    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)
    return school, section, assignment, enrolled, nonmember, staff


def _bulk_url(section, assignment):
    return f"/api/v1/gradebook/sections/{section.id}/assignments/{assignment.id}/grades/upsert/"


def _patch_url(entry):
    return f"/api/v1/gradebook/grade-entries/{entry.id}/"


def test_bulk_rejects_nonmember_and_writes_nothing():
    school, section, assignment, enrolled, nonmember, _staff = _graph()
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar@gradebook.test")
    client = APIClient()
    client.force_authenticate(registrar)

    response = client.post(
        _bulk_url(section, assignment),
        {"grades": [
            {"student_id": str(enrolled.id), "points_earned": 91},
            {"student_id": str(nonmember.id), "points_earned": 88},
        ]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 400
    assert GradeEntry.objects.count() == 0


def test_bulk_rejects_malformed_row_atomically():
    school, section, assignment, enrolled, _nonmember, _staff = _graph()
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar2@gradebook.test")
    client = APIClient()
    client.force_authenticate(registrar)

    response = client.post(
        _bulk_url(section, assignment),
        {"grades": [
            {"student_id": str(enrolled.id), "points_earned": 91},
            {"points_earned": 88},
        ]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 400
    assert GradeEntry.objects.count() == 0


def test_bulk_rejects_legacy_admin_role():
    school, section, assignment, enrolled, _nonmember, _staff = _graph()
    legacy_admin = _user(school=school, role_code="ADMIN", email="legacy-admin@gradebook.test")
    client = APIClient()
    client.force_authenticate(legacy_admin)

    response = client.post(
        _bulk_url(section, assignment),
        {"grades": [{"student_id": str(enrolled.id), "points_earned": 91}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403
    assert GradeEntry.objects.count() == 0


def test_patch_allows_assigned_teacher_for_enrolled_student():
    school, section, assignment, enrolled, _nonmember, staff = _graph()
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=enrolled,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=80,
        points_possible=100,
    )
    teacher = _user(school=school, role_code="TEACHER", email=staff.email, staff=staff)
    client = APIClient()
    client.force_authenticate(teacher)

    response = client.patch(
        _patch_url(entry),
        {"points_earned": 95},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    entry.refresh_from_db()
    assert entry.points_earned == 95


def test_patch_denies_unassigned_teacher():
    school, section, assignment, enrolled, _nonmember, _staff = _graph()
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=enrolled,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=80,
        points_possible=100,
    )
    other_staff = Staff.objects.create(
        school=school,
        first_name="Other",
        last_name="Teacher",
        email="other.teacher@gradebook.test",
        role_type="TEACHER",
        status="ACTIVE",
    )
    teacher = _user(
        school=school,
        role_code="TEACHER",
        email=other_staff.email,
        staff=other_staff,
    )
    client = APIClient()
    client.force_authenticate(teacher)

    response = client.patch(
        _patch_url(entry),
        {"points_earned": 95},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 404
    entry.refresh_from_db()
    assert entry.points_earned == 80


def test_patch_revalidates_roster_membership():
    school, section, assignment, _enrolled, nonmember, _staff = _graph()
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=nonmember,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=80,
        points_possible=100,
    )
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar3@gradebook.test")
    client = APIClient()
    client.force_authenticate(registrar)

    response = client.patch(
        _patch_url(entry),
        {"points_earned": 95},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 400
    entry.refresh_from_db()
    assert entry.points_earned == 80
