"""DB-backed camp family privacy: canonical guardian-to-household membership only."""
from datetime import date, time

import pytest
from rest_framework.test import APIClient

from core.models import School, UserAccount
from households.models import Guardian, Household, Student
from summer_camp.models import SummerCampEnrollment, SummerCampProgram, SummerCampSession

pytestmark = pytest.mark.django_db


def _child(school, suffix):
    family = Household.objects.create(school_id=school.id, name=f"Guardian Family {suffix}")
    child = Student.objects.create(
        school_id=school.id, household=family,
        first_name="Synthetic", last_name=suffix, grade_level="4",
    )
    return family, child


def test_parent_can_view_only_verified_household_camper_in_same_school():
    school = School.objects.create(name="Parent Camp School")
    own_family, own_child = _child(school, "Own")
    other_family, other_child = _child(school, "Unrelated")
    program = SummerCampProgram.objects.create(school=school, name="School Summer Program")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="July",
        start_date=date(2026, 7, 1), end_date=date(2026, 7, 10),
        start_time=time(8, 0), end_time=time(16, 0), capacity=25, status="PUBLISHED",
    )
    for child in (own_child, other_child):
        SummerCampEnrollment.objects.create(
            school=school, session=session, student=child, household_id=child.household_id,
            status="REGISTERED",
        )
    parent = UserAccount.objects.create_user(
        username="synthetic-parent-camp", email="parent-camp@example.test", school=school, password="synthetic", is_staff=False,
    )
    Guardian.objects.create(
        school_id=school.id, household=own_family,
        account=parent, first_name="Linked", last_name="Guardian",
    )
    outsider = UserAccount.objects.create_user(
        username="synthetic-unlinked-camp", email="unlinked-camp@example.test", school=school, password="synthetic", is_staff=False,
    )
    client = APIClient()
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    client.force_authenticate(user=parent)

    own = client.get(f"/api/v1/summer-camp/parent/{own_child.id}/")
    assert own.status_code == 200, own.data
    assert own.data["student_id"] == str(own_child.id)
    assert len(own.data["rows"]) == 1
    assert own.data["rows"][0]["enrollment_id"] is not None

    denied = client.get(f"/api/v1/summer-camp/parent/{other_child.id}/")
    assert denied.status_code == 403
    assert denied.data == {"detail": "Forbidden"}

    client.force_authenticate(user=outsider)
    assert client.get(f"/api/v1/summer-camp/parent/{own_child.id}/").status_code == 403
    assert SummerCampEnrollment.objects.filter(school=school).count() == 2
