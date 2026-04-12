from datetime import date
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Family, School, Student as CoreStudent
from households.models import Household, Student as HouseholdStudent


pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str, first_name: str = "", last_name: str = ""):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"student360-{uuid.uuid4()}",
        email=email,
        password="pass12345!",
        first_name=first_name,
        last_name=last_name,
        is_staff=True,
    )
    if hasattr(user, "school_id"):
        user.school = school
        user.save(update_fields=["school"])
    return user


def test_student_overview_returns_200_for_core_student():
    school = School.objects.create(name="Student360 Overview School")
    family = Family.objects.create(school=school, family_name="Overview Family")
    student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-360-001",
        first_name="Casey",
        last_name="Core",
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    user = _mk_user(school=school, email="overview@test.local")

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        f"/api/v1/360/students/{student.id}/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(student.id)


def test_student_self_overview_resolves_households_student_profile():
    school = School.objects.create(name="Student360 Self School")
    household = Household.objects.create(school_id=school.id, name="Stone Household")
    HouseholdStudent.objects.create(
        school_id=school.id,
        household=household,
        first_name="Harper",
        last_name="Stone",
        grade_level="9",
    )
    user = _mk_user(
        school=school,
        email="harper.stone@test.local",
        first_name="Harper",
        last_name="Stone",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["name"] == "Harper Stone"
