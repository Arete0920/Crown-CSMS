import uuid
from datetime import date
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, School, Staff, UserRole
from households.models import Guardian, Household, Student
from academics.models import Course, Section, TeacherAssignment, Term


pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str, is_staff: bool = False):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="pass12345!",
        is_staff=is_staff,
        school=school,
    )
    return user


def _assign_role(*, user, school: School, role_code: str):
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def test_academics_list_years_scoped():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")

    AcademicYear.objects.create(
        school=school_a,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 10),
        is_current=True,
    )
    AcademicYear.objects.create(
        school=school_b,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 10),
        is_current=True,
    )

    user = _mk_user(school=school_a, email="staff@a.test", is_staff=True)

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get("/api/v1/academics/years/")

    assert resp.status_code == 200
    payload = resp.json()
    results = payload["results"]
    assert results
    assert all(r["school_id"] == str(school_a.id) for r in results)


def test_sections_filter_by_term():
    school = School.objects.create(name="School A")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 10),
        is_current=True,
    )
    term_fall = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall 2026",
        active=True,
    )
    term_spring = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2027-SPRING",
        name="Spring 2027",
        active=True,
    )
    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")

    Section.objects.create(
        school_id=school.id,
        course=course,
        term=term_fall.code,
        term_ref=term_fall,
        teacher_name="Mrs. A",
    )
    Section.objects.create(
        school_id=school.id,
        course=course,
        term=term_spring.code,
        term_ref=term_spring,
        teacher_name="Mrs. B",
    )

    user = _mk_user(school=school, email="staff@a.test", is_staff=True)
    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/academics/sections/?term_id={term_fall.id}")
    assert resp.status_code == 200
    payload = resp.json()
    results = payload["results"]
    assert len(results) == 1
    assert results[0]["term_id"] == str(term_fall.id)


def test_teacher_only_sees_own_sections():
    school = School.objects.create(name="School A")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 10),
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall 2026",
        active=True,
    )
    course = Course.objects.create(school_id=school.id, code="ENG-201", name="English")

    section_a = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher A",
    )
    section_b = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher B",
    )

    staff_a = Staff.objects.create(
        school=school,
        first_name="Teach",
        last_name="A",
        email="teach.a@example.com",
        role_type="TEACHER",
        status="ACTIVE",
    )
    staff_b = Staff.objects.create(
        school=school,
        first_name="Teach",
        last_name="B",
        email="teach.b@example.com",
        role_type="TEACHER",
        status="ACTIVE",
    )

    TeacherAssignment.objects.create(school_id=school.id, section=section_a, staff=staff_a)
    TeacherAssignment.objects.create(school_id=school.id, section=section_b, staff=staff_b)

    user = _mk_user(school=school, email="teach.a@example.com", is_staff=False)
    user.staff = staff_a
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/academics/sections/")
    assert resp.status_code == 200
    payload = resp.json()
    results = payload["results"]
    assert len(results) == 1
    assert results[0]["section_id"] == str(section_a.id)


def test_parent_only_sees_linked_students():
    school = School.objects.create(name="School A")
    user = _mk_user(school=school, email="parent@example.com", is_staff=False)
    _assign_role(user=user, school=school, role_code="PARENT")

    household_a = Household.objects.create(school_id=school.id, name="Household A")
    household_b = Household.objects.create(school_id=school.id, name="Household B")

    Guardian.objects.create(
        school_id=school.id,
        household=household_a,
        first_name="Pat",
        last_name="Parent",
        email="parent@example.com",
    )

    student_a = Student.objects.create(
        school_id=school.id,
        household=household_a,
        first_name="Amy",
        last_name="Adams",
        grade_level="5",
    )
    Student.objects.create(
        school_id=school.id,
        household=household_b,
        first_name="Bobby",
        last_name="Brown",
        grade_level="4",
    )

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/academics/parents/me/students/")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["student_id"] == str(student_a.id)
