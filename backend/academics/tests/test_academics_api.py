import uuid
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household, Student
from academics.models import Course, Section


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

    # minimal student record (must match your Student model fields)
    st = Student.objects.create(
        school_id=school.id,
        household=hh,
        first_name="Amy",
        last_name="Adams",
        grade_level="5",
        is_active=True,
    )

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    # create course
    resp = c.post(
        "/api/v1/academics/courses/",
        data={"code": "MATH5", "name": "Math 5"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    course_id = resp.json()["data"]["id"]
    assert Course.objects.filter(id=course_id).count() == 1

    # create section
    resp = c.post(
        "/api/v1/academics/sections/",
        data={"course_id": course_id, "term": "2026-FALL", "teacher_name": "Mrs. Smith"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    section_id = resp.json()["data"]["id"]
    assert Section.objects.filter(id=section_id).count() == 1

    # enroll
    resp = c.post(
        "/api/v1/academics/enroll/",
        data={"section_id": section_id, "student_id": str(st.id)},
        content_type="application/json",
    )
    assert resp.status_code == 201

    # roster
    resp = c.get(f"/api/v1/academics/sections/{section_id}/roster/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert len(body["data"]["students"]) == 1
