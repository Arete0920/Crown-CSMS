import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, School, Staff, UserRole
from households.models import Household, Student
from academics.models import Assignment, AssignmentCategory, Course, Enrollment, Section, Term, TeacherAssignment
from gradebook.models import GradeEntry


pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str, is_staff: bool = False):
    User = get_user_model()
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="pass12345!",
        is_staff=is_staff,
        school=school,
    )


def _assign_role(*, user, school: School, role_code: str):
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _seed_section(*, school: School, staff_email: str):
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
    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher A",
    )

    staff = Staff.objects.create(
        school=school,
        first_name="Teach",
        last_name="A",
        email=staff_email,
        role_type="TEACHER",
        status="ACTIVE",
    )
    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)

    return section, staff


def test_teacher_can_list_sections():
    school = School.objects.create(name="School A")
    section, staff = _seed_section(school=school, staff_email="teach.a@example.com")

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/gradebook/sections/")
    assert resp.status_code == 200
    payload = resp.json()
    results = payload["results"]
    assert len(results) == 1
    assert results[0]["section_id"] == str(section.id)


def test_teacher_can_get_grades_grid():
    school = School.objects.create(name="School A")
    section, staff = _seed_section(school=school, staff_email="teach.a@example.com")

    household = Household.objects.create(school_id=school.id, name="Household A")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Amy",
        last_name="Adams",
        grade_level="5",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)

    GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment_name="Quiz 1",
        points_earned=9,
        points_possible=10,
    )

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/sections/{section.id}/grades/")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["section_id"] == str(section.id)
    assert payload["assignments"]
    assert payload["rows"]
    assert payload["rows"][0]["student"]["student_id"] == str(student.id)


def test_non_teacher_role_forbidden():
    school = School.objects.create(name="School A")
    _seed_section(school=school, staff_email="teach.a@example.com")

    user = _mk_user(school=school, email="parent@example.com", is_staff=False)
    _assign_role(user=user, school=school, role_code="PARENT")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/gradebook/sections/")
    assert resp.status_code == 403



def test_teacher_grades_grid_includes_published_assignment_without_scores():
    school = School.objects.create(name="School Z")
    section, staff = _seed_section(school=school, staff_email="teach.z@example.com")

    household = Household.objects.create(school_id=school.id, name="Household Z")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Nina",
        last_name="North",
        grade_level="5",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)

    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Projects",
        weight_percent=100,
        sort_order=1,
        is_active=True,
    )
    Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name="Virtual Lab",
        points_possible=15,
        is_published=True,
    )

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/sections/{section.id}/grades/")
    assert resp.status_code == 200
    payload = resp.json()
    assignment_names = {a["assignment_name"] for a in payload["assignments"]}
    assert "Virtual Lab" in assignment_names

    score = payload["rows"][0]["scores"]["Virtual Lab"]
    assert score["points_earned"] is None
