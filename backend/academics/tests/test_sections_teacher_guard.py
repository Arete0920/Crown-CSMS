import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, Term, TeacherAssignment
from core.models import AcademicYear, School, Staff, UserRole
from households.models import Household, Student


pytestmark = pytest.mark.django_db

User = get_user_model()


def test_teacher_cannot_query_other_teacher_id():
    """
    If user has TEACHER role, they may not pass another teacher_id.
    Expect empty list.
    """
    school = School.objects.create(name="Test School")

    # Create staff 1
    staff_teacher1 = Staff.objects.create(
        school=school,
        first_name="Teacher",
        last_name="One",
        email="teacher1@test.com",
        role_type="TEACHER",
    )
    # Create teacher 1 user (the authenticated user) linked to staff1
    teacher1_user = User.objects.create_user(
        username=f"teacher1-{uuid.uuid4()}",
        email="teacher1@test.com",
        password="pass12345!",
        school=school,
        staff=staff_teacher1,
    )
    UserRole.objects.create(
        user=teacher1_user,
        school=school,
        role_code="TEACHER",
    )

    # Create staff 2
    staff_teacher2 = Staff.objects.create(
        school=school,
        first_name="Teacher",
        last_name="Two",
        email="teacher2@test.com",
        role_type="TEACHER",
    )
    # Create teacher 2 user (the other teacher) linked to staff2
    teacher2_user = User.objects.create_user(
        username=f"teacher2-{uuid.uuid4()}",
        email="teacher2@test.com",
        password="pass12345!",
        school=school,
        staff=staff_teacher2,
    )

    # Create a section assigned to teacher2
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
        code="MATH-101",
        name="Math 101",
        department="Mathematics",
        credits="1.00",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
        teacher=teacher2_user,
        teacher_name="Teacher Two",
    )
    TeacherAssignment.objects.create(
        school_id=school.id,
        section=section,
        staff=staff_teacher2,
    )

    # Teacher1 tries to query sections with teacher2's staff ID
    client = APIClient()
    client.force_authenticate(user=teacher1_user)

    url = f"/api/v1/academics/sections/?teacher_id={staff_teacher2.id}"
    resp = client.get(url, HTTP_X_SCHOOL_ID=str(school.id))

    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert body["total"] == 0
    assert len(body["results"]) == 0
