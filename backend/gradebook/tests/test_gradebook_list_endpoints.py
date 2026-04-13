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


def _seed_section_with_data(*, school: School, staff_email: str):
    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name="2026-2027",
        defaults={
            "start_date": "2026-08-15",
            "end_date": "2027-06-10",
            "is_current": True,
        },
    )
    term, _ = Term.objects.get_or_create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        defaults={
            "name": "Fall 2026",
            "active": True,
        },
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

    return section, staff, student


def test_assignments_list_requires_section_id():
    school = School.objects.create(name="School A")
    section, staff, student = _seed_section_with_data(school=school, staff_email="teach.a@example.com")

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/gradebook/assignments/")
    assert resp.status_code == 400
    assert "section_id is required" in resp.json()["detail"]


def test_students_list_requires_section_id():
    school = School.objects.create(name="School B")
    section, staff, student = _seed_section_with_data(school=school, staff_email="teach.b@example.com")

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get("/api/v1/gradebook/students/")
    assert resp.status_code == 400
    assert "section_id is required" in resp.json()["detail"]


def test_assignments_list_teacher_can_access():
    school = School.objects.create(name="School C")
    section, staff, student = _seed_section_with_data(school=school, staff_email="teach.c@example.com")

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/assignments/?section_id={section.id}")
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["assignment_name"] == "Quiz 1"


def test_students_list_teacher_can_access():
    school = School.objects.create(name="School D")
    section, staff, student = _seed_section_with_data(school=school, staff_email="teach.d@example.com")

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/students/?section_id={section.id}")
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["student__first_name"] == "Amy"
    assert payload[0]["student__last_name"] == "Adams"


def test_assignments_list_non_teacher_role_forbidden():
    school = School.objects.create(name="School E")
    section, staff, student = _seed_section_with_data(school=school, staff_email="teach.e@example.com")

    user = _mk_user(school=school, email="parent@example.com", is_staff=False)
    _assign_role(user=user, school=school, role_code="PARENT")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/assignments/?section_id={section.id}")
    assert resp.status_code == 403


def test_students_list_non_teacher_role_forbidden():
    school = School.objects.create(name="School F")
    section, staff, student = _seed_section_with_data(school=school, staff_email="teach.f@example.com")

    user = _mk_user(school=school, email="parent2@example.com", is_staff=False)
    _assign_role(user=user, school=school, role_code="PARENT")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/students/?section_id={section.id}")
    assert resp.status_code == 403


def test_assignments_list_teacher_cannot_see_other_sections():
    school = School.objects.create(name="School G")
    section1, staff1, student1 = _seed_section_with_data(school=school, staff_email="teach.g1@example.com")
    section2, staff2, student2 = _seed_section_with_data(school=school, staff_email="teach.g2@example.com")

    user = _mk_user(school=school, email=staff1.email, is_staff=False)
    user.staff = staff1
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    # Teacher 1 can access their own section
    resp = client.get(f"/api/v1/gradebook/assignments/?section_id={section1.id}")
    assert resp.status_code == 200

    # Teacher 1 cannot access Teacher 2's section
    resp = client.get(f"/api/v1/gradebook/assignments/?section_id={section2.id}")
    assert resp.status_code == 404


def test_students_list_teacher_cannot_see_other_sections():
    school = School.objects.create(name="School H")
    section1, staff1, student1 = _seed_section_with_data(school=school, staff_email="teach.h1@example.com")
    section2, staff2, student2 = _seed_section_with_data(school=school, staff_email="teach.h2@example.com")

    user = _mk_user(school=school, email=staff1.email, is_staff=False)
    user.staff = staff1
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    # Teacher 1 can access their own section
    resp = client.get(f"/api/v1/gradebook/students/?section_id={section1.id}")
    assert resp.status_code == 200

    # Teacher 1 cannot access Teacher 2's section
    resp = client.get(f"/api/v1/gradebook/students/?section_id={section2.id}")
    assert resp.status_code == 404



def test_students_list_includes_enrolled_student_without_grades():
    school = School.objects.create(name="School I")
    section, staff, student_with_grade = _seed_section_with_data(school=school, staff_email="teach.i@example.com")

    household = Household.objects.create(school_id=school.id, name="Household B")
    student_without_grade = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Ben",
        last_name="Brooks",
        grade_level="5",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student_without_grade)

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/students/?section_id={section.id}")
    assert resp.status_code == 200
    payload = resp.json()
    student_ids = {item["student_id"] for item in payload}
    assert str(student_with_grade.id) in student_ids
    assert str(student_without_grade.id) in student_ids


def test_assignments_list_includes_published_assignment_without_grade_entries():
    school = School.objects.create(name="School J")
    section, staff, _ = _seed_section_with_data(school=school, staff_email="teach.j@example.com")

    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=100,
        sort_order=1,
        is_active=True,
    )
    Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name="Online Module 1",
        points_possible=20,
        is_published=True,
    )

    user = _mk_user(school=school, email=staff.email, is_staff=False)
    user.staff = staff
    user.save(update_fields=["staff"])
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(f"/api/v1/gradebook/assignments/?section_id={section.id}")
    assert resp.status_code == 200
    payload = resp.json()
    names = {item["assignment_name"] for item in payload}
    assert "Online Module 1" in names
