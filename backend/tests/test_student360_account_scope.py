import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from core.models import School
from households.models import Household, Student

pytestmark = pytest.mark.django_db
User = get_user_model()


def _user(school, prefix):
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.test"
    return User.objects.create_user(username=email, email=email, password="not-used", school=school)


def test_student360_self_and_detail_require_canonical_account_link():
    school = School.objects.create(name=f"Student Scope {uuid.uuid4().hex[:8]}")
    household = Household.objects.create(school_id=school.id, name="Scope Household")
    student_user = _user(school, "student")
    outsider = _user(school, "outsider")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        account=student_user,
        first_name="Avery",
        last_name="Scope",
        grade_level="7",
    )

    client = APIClient()
    client.force_authenticate(user=student_user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    self_response = client.get("/api/v1/360/me/overview/")
    assert self_response.status_code == 200, self_response.content
    assert self_response.json()["student"]["id"] == str(student.id)

    client.force_authenticate(user=outsider)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    assert client.get("/api/v1/360/me/overview/").status_code == 404
    assert client.get(f"/api/v1/360/students/{student.id}/overview/").status_code == 404


def test_student_account_link_rejects_cross_school_account():
    school = School.objects.create(name=f"Student School A {uuid.uuid4().hex[:8]}")
    other_school = School.objects.create(name=f"Student School B {uuid.uuid4().hex[:8]}")
    household = Household.objects.create(school_id=school.id, name="Scope Household")
    wrong_school_user = _user(other_school, "wrong-school")

    with pytest.raises(ValidationError):
        Student.objects.create(
            school_id=school.id,
            household=household,
            account=wrong_school_user,
            first_name="Cross",
            last_name="Tenant",
            grade_level="8",
        )
