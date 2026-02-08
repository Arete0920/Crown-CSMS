import uuid
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from core.models import AcademicYear, School
from households.models import Household, Student
from academics.models import Course, Section, Term


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_create_course_section_enroll_and_roster():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    # read-only endpoints should reject writes
    resp = c.post(
        "/api/v1/academics/courses/",
        data={"code": "MATH5", "name": "Math 5"},
        content_type="application/json",
    )
    assert resp.status_code == 405

    resp = c.post(
        "/api/v1/academics/sections/",
        data={"course_id": str(uuid.uuid4()), "term": "2026-FALL", "teacher_name": "Mrs. Smith"},
        content_type="application/json",
    )
    assert resp.status_code == 405

    resp = c.post(
        "/api/v1/academics/enroll/",
        data={"section_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())},
        content_type="application/json",
    )
    assert resp.status_code == 404


def test_courses_list_includes_spine_fields():
    school = School.objects.create(name="Test School")
    user = _mk_user_with_school(school)
    user.is_staff = True
    user.save(update_fields=["is_staff"])

    Course.objects.create(
        school_id=school.id,
        code="ENG-101",
        name="English 9",
        department="English",
        credits="1.00",
    )

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get("/api/v1/academics/courses/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"], body
    row = body["results"][0]
    assert row["code"] == "ENG-101"
    assert row["department"] == "English"
    assert row["credits"] == "1.00"


def test_terms_list_includes_spine_fields():
    school = School.objects.create(name="Test School")
    user = _mk_user_with_school(school)
    user.is_staff = True
    user.save(update_fields=["is_staff"])

    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall",
        school_year="2026-2027",
        ordering=1,
        active=True,
    )

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get("/api/v1/academics/terms/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"], body
    row = body["results"][0]
    assert row["school_year"] == "2026-2027"
    assert row["ordering"] == 1
