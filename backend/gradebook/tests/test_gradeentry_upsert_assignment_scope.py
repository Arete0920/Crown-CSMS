import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Assignment, AssignmentCategory, Course, Enrollment, Section, TeacherAssignment, Term
from core.models import AcademicYear, School, Staff, UserRole
from gradebook.models import GradeEntry
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


def _add_student(*, school: School, name: str):
    household = Household.objects.create(school_id=school.id, name=f"{name} Household")
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name=name,
        last_name="Student",
        grade_level="5",
    )


def _upsert_url(section_id, assignment_id):
    return f"/api/v1/gradebook/sections/{section_id}/assignments/{assignment_id}/grades/upsert/"


def _patch_url(entry_id):
    return f"/api/v1/gradebook/grade-entries/{entry_id}/"


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


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

    resp = _client_for(user).post(
        _upsert_url(section.id, assignment.id),
        {"grades": [{"student_id": str(student.id), "points_earned": 8.5}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

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

    resp = _client_for(user).post(
        _upsert_url(section.id, assignment.id),
        {"grades": [{"student_id": str(student.id), "points_earned": 8.5}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 404, resp.content
    assert GradeEntry.objects.count() == 0


def test_grade_upsert_allows_registrar_without_teacher_assignment():
    school = School.objects.create(name="Scope School")
    section, _assigned_staff, student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )

    registrar = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=registrar, school=school, role_code="REGISTRAR")

    resp = _client_for(registrar).post(
        _upsert_url(section.id, assignment.id),
        {"grades": [{"student_id": str(student.id), "points_earned": 9.0}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 200, resp.content
    assert resp.json().get("count") == 1


def test_grade_upsert_rejects_nonmember_without_write():
    school = School.objects.create(name="Roster School")
    section, _staff, _student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )
    outsider = _add_student(school=school, name="Outsider")
    registrar = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=registrar, school=school, role_code="REGISTRAR")

    resp = _client_for(registrar).post(
        _upsert_url(section.id, assignment.id),
        {"grades": [{"student_id": str(outsider.id), "points_earned": 7}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 400, resp.content
    assert GradeEntry.objects.count() == 0


def test_grade_upsert_rejects_entire_batch_when_any_row_is_invalid():
    school = School.objects.create(name="Atomic School")
    section, _staff, student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )
    registrar = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=registrar, school=school, role_code="REGISTRAR")

    resp = _client_for(registrar).post(
        _upsert_url(section.id, assignment.id),
        {
            "grades": [
                {"student_id": str(student.id), "points_earned": 8},
                {"student_id": str(uuid.uuid4()), "points_earned": 9},
            ]
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 400, resp.content
    assert GradeEntry.objects.count() == 0


def test_patch_requires_gradebook_edit_permission():
    school = School.objects.create(name="Patch Permission School")
    section, _staff, student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment=assignment,
        assignment_name=assignment.name,
        points_possible=assignment.points_possible,
        points_earned=5,
    )
    support = _mk_user(school=school, email="support@test.local")
    _assign_role(user=support, school=school, role_code="SUPPORT")

    resp = _client_for(support).patch(
        _patch_url(entry.id),
        {"points_earned": 9},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 403, resp.content
    entry.refresh_from_db()
    assert entry.points_earned == 5


def test_patch_revalidates_roster_membership():
    school = School.objects.create(name="Patch Roster School")
    section, _staff, _student, assignment = _seed_gradebook_section(
        school=school,
        teacher_name="Assigned",
        teacher_email="assigned.teacher@test.local",
    )
    outsider = _add_student(school=school, name="Outsider")
    entry = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=outsider,
        assignment=assignment,
        assignment_name=assignment.name,
        points_possible=assignment.points_possible,
        points_earned=5,
    )
    registrar = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=registrar, school=school, role_code="REGISTRAR")

    resp = _client_for(registrar).patch(
        _patch_url(entry.id),
        {"points_earned": 9},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 400, resp.content
    entry.refresh_from_db()
    assert entry.points_earned == 5
