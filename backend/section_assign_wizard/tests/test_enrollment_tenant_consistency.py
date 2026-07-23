import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import School
from households.models import Household, Student

pytestmark = pytest.mark.django_db
BASE_URL = "/api/v1/section-assign-wizard/sessions/"


def _school(name):
    return School.objects.create(name=name, timezone="America/New_York", is_active=True)


def _student(school):
    household = Household.objects.create(school_id=school.id, name=f"HH-{uuid.uuid4()}")
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name="Student",
    )


def _section(school):
    course = Course.objects.create(
        school_id=school.id,
        code=f"COURSE-{uuid.uuid4().hex[:6]}",
        name="Course",
    )
    return Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )


def _client(school):
    user = get_user_model().objects.create_user(
        username=f"user-{uuid.uuid4()}",
        password="test-pass",
        school=school,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _stage(client, school, section, student):
    headers = {"HTTP_X_SCHOOL_ID": str(school.id)}
    created = client.post(BASE_URL, **headers)
    session_id = created.data["session_id"]
    configured = client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"section_id": str(section.id), "term": section.term},
        format="json",
        **headers,
    )
    assert configured.status_code == 200
    loaded = client.post(
        f"{BASE_URL}{session_id}/load/",
        {"student_ids": [str(student.id)]},
        format="json",
        **headers,
    )
    assert loaded.status_code == 200
    staged = client.post(
        f"{BASE_URL}{session_id}/stage/",
        {"changes": [{"student_id": str(student.id), "action": "add"}]},
        format="json",
        **headers,
    )
    assert staged.status_code == 200
    return session_id, headers


def test_commit_accepts_same_school_student():
    school = _school("Same School")
    student = _student(school)
    section = _section(school)
    client = _client(school)
    session_id, headers = _stage(client, school, section, student)

    response = client.post(
        f"{BASE_URL}{session_id}/commit/",
        {"confirm": True},
        format="json",
        **headers,
    )

    assert response.status_code == 200
    assert response.data["enrolled"] == 1
    assert Enrollment.objects.filter(
        school_id=school.id,
        section=section,
        student=student,
    ).exists()


def test_commit_rejects_cross_school_student_without_persistence():
    school_a = _school("School A")
    school_b = _school("School B")
    student_b = _student(school_b)
    section_a = _section(school_a)
    client = _client(school_a)
    session_id, headers = _stage(client, school_a, section_a, student_b)

    response = client.post(
        f"{BASE_URL}{session_id}/commit/",
        {"confirm": True},
        format="json",
        **headers,
    )

    assert response.status_code == 404
    assert not Enrollment.objects.filter(
        section=section_a,
        student=student_b,
    ).exists()
