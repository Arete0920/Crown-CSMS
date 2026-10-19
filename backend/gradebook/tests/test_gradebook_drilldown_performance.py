"""Keep gradebook drilldown SQL cost independent of section roster size."""
import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from core.models import School, UserRole
from households.models import Household, Student
from academics.models import Enrollment
from gradebook.tests.test_gradebook_drilldown import _mk_user, _assign_role, _seed_academics_data


pytestmark = pytest.mark.django_db


def _client(school):
    user = _mk_user(school=school, email=f"grade-query-{uuid.uuid4()}@example.test")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_gradebook_drilldown_does_not_query_per_student():
    school = School.objects.create(name=f"Grade query {uuid.uuid4()}")
    section, students = _seed_academics_data(school)
    client = _client(school)
    url = f"/api/v1/gradebook/sections/{section.id}/drilldown/?limit=200"

    with CaptureQueriesContext(connection) as small:
        first = client.get(url, HTTP_X_SCHOOL_ID=str(school.id))
    assert first.status_code == 200, first.content

    household = Household.objects.filter(school_id=school.id).first()
    for index in range(18):
        student = Student.objects.create(
            school_id=school.id, household=household,
            first_name=f"Extra{index}", last_name="Roster", grade_level="5",
        )
        Enrollment.objects.create(school_id=school.id, section=section, student=student)

    with CaptureQueriesContext(connection) as large:
        second = client.get(url, HTTP_X_SCHOOL_ID=str(school.id))
    assert second.status_code == 200, second.content
    assert len(second.json()["rows"]) == len(students) + 18
    assert len(large) <= len(small) + 2, (len(small), len(large))
    assert len(large) < 30


@pytest.mark.parametrize("threshold", ["NaN", "inf", "-inf", "n/a"])
def test_gradebook_drilldown_rejects_non_finite_thresholds(threshold):
    school = School.objects.create(name=f"Grade threshold {uuid.uuid4()}")
    section, _ = _seed_academics_data(school)
    client = _client(school)
    response = client.get(
        f"/api/v1/gradebook/sections/{section.id}/drilldown/",
        {"threshold": threshold}, HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 400
    assert "finite" in response.json()["detail"]
