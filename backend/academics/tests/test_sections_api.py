import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, Term
from core.models import AcademicYear, School
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _mk_staff_user(school: School):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        password="pass12345!",
        school=school,
        is_staff=True,
    )
    return user


def _seed_section(*, school: School, teacher=None):
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
        name="Fall",
        school_year="2026-2027",
        ordering=1,
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code="ENG-101",
        name="English 9",
        department="English",
        credits="1.00",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
        teacher=teacher,
        teacher_name="Mrs. Smith",
    )
    household = Household.objects.create(school_id=school.id, name="Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Jane",
        last_name="Doe",
        grade_level="9",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    return section, student


def test_sections_list_returns_200():
    """Test GET /api/v1/academics/sections/ returns 200."""
    school = School.objects.create(name="Test School")
    user = _mk_staff_user(school)
    section, _student = _seed_section(school=school, teacher=user)

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get("/api/v1/academics/sections/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert body["total"] >= 1


def test_sections_detail_returns_200():
    """Test GET /api/v1/academics/sections/{id}/ returns 200."""
    school = School.objects.create(name="Test School")
    user = _mk_staff_user(school)
    section, _student = _seed_section(school=school, teacher=user)

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["section_id"] == str(section.id)
    assert body["course_code"] == "ENG-101"


def test_section_roster_returns_students():
    """Test GET /api/v1/academics/sections/{id}/roster/ returns students."""
    school = School.objects.create(name="Test School")
    user = _mk_staff_user(school)
    section, student = _seed_section(school=school, teacher=user)

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get(
        f"/api/v1/academics/sections/{section.id}/roster/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["section_id"] == str(section.id)
    assert body["counts"]["students"] == 1
    assert body["students"][0]["student_id"] == str(student.id)
    # name format is "LastName, FirstName"
    assert "Doe" in body["students"][0]["name"]


def test_section_post_returns_405():
    """Test POST /api/v1/academics/sections/ returns 405 (Method Not Allowed)."""
    school = School.objects.create(name="Test School")
    user = _mk_staff_user(school)

    client = APIClient()
    client.force_authenticate(user)
    resp = client.post(
        "/api/v1/academics/sections/",
        data={"course_id": str(uuid.uuid4()), "term": "2026-FALL"},
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 405
