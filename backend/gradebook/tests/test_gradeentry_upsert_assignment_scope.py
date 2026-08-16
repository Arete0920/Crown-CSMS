import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Assignment, AssignmentCategory, Course, Enrollment, Section, TeacherAssignment, Term
from core.models import AcademicYear, School, Staff, UserRole
from households.models import Household, Student

pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str):
    User = get_user_model()
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )


def _assign_role(*, user, school: School, role_code: str):
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _seed_gradebook_section(*, school: School, teacher_name: str, teacher_email: str):
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
        name="Mathematics",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name=teacher_name,
    )

    staff = Staff.objects.create(
        school=school,
        first_name=teacher_name,
        last_name="Teacher",
        email=teacher_email,
        role_type="TEACHER",
        status="ACTIVE",
    )

    household = Household.objects.create(school_id=school.id, name="Gradebook Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Student",
        last_name="One",
        grade_level="5",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)

    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Quizzes",
        weight_percent=100,
        sort_order=1,
        is_active=True,
    )

    assignment = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name="Quiz 1",
        points_possible="10.0",
        is_published=True,
    )

    return section, staff, student, assignment


def _upsert_url(section_id, assignment_id):
    return f"/api/v1/gradebook/sections/{section_id}/assignments/{assignment_id}/grades/upsert/"


def test_grade_upsert_allows_assigned_teacher():
    school = School.objects.create(name="Scope School")
    section, assigned_staff, student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )
    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=assigned_staff)

    user = _mk_user(school=school, email=assigned_staff.email)
    user.staff = assigned_staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    payload = {"grades": [{"student_id": str(student.id), "points_earned": 8.5}]}
    resp = client.post(_upsert_url(section.id, assignment.id), payload, format="json", HTTP_X_SCHOOL_ID=str(school.id))

    assert resp.status_code == 200, resp.content
    assert resp.json().get("count") == 1


def test_grade_upsert_denies_unassigned_teacher_section_access():
    school = School.objects.create(name="Scope School")
    section, assigned_staff, student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )
    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=assigned_staff)

    unassigned_staff = Staff.objects.create(
        school=school,
        first_name="Unassigned",
        last_name="Teacher",
        email="unassigned.teacher@test.local",
        role_type="TEACHER",
        status="ACTIVE",
    )

    user = _mk_user(school=school, email=unassigned_staff.email)
    user.staff = unassigned_staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    payload = {"grades": [{"student_id": str(student.id), "points_earned": 8.5}]}
    resp = client.post(_upsert_url(section.id, assignment.id), payload, format="json", HTTP_X_SCHOOL_ID=str(school.id))

    assert resp.status_code == 404, resp.content


def test_grade_upsert_allows_registrar_without_teacher_assignment():
    school = School.objects.create(name="Scope School")
    section, _assigned_staff, student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )

    registrar = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=registrar, school=school, role_code="REGISTRAR")

    client = APIClient()
    client.force_authenticate(registrar)

    payload = {"grades": [{"student_id": str(student.id), "points_earned": 9.0}]}
    resp = client.post(_upsert_url(section.id, assignment.id), payload, format="json", HTTP_X_SCHOOL_ID=str(school.id))

    assert resp.status_code == 200, resp.content
    assert resp.json().get("count") == 1
