"""Parent Camp API must require a linked guardian and same-school child."""
from datetime import date, time
import pytest
from rest_framework.test import APIClient
from core.models import School, UserAccount
from households.models import Guardian, Household, Student
from summer_camp.models import SummerCampEnrollment, SummerCampProgram, SummerCampSession

pytestmark = pytest.mark.django_db


def test_linked_guardian_sees_only_own_child_without_cross_family_disclosure():
    school = School.objects.create(name="Parent Camp School")
    families = [Household.objects.create(school_id=school.id, name=f"Family {i}") for i in (1, 2)]
    children = [Student.objects.create(school_id=school.id, household=family,
                first_name="Synthetic", last_name=f"Camper {i}", grade_level="4")
                for i, family in enumerate(families)]
    program = SummerCampProgram.objects.create(school=school, name="Summer Program")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="July", start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 10), start_time=time(8), end_time=time(16),
        capacity=25, status="PUBLISHED",
    )
    for child in children:
        SummerCampEnrollment.objects.create(
            school=school, session=session, student=child, household=child.household,
            status="REGISTERED",
        )
    linked = UserAccount.objects.create_user(username="linked-parent", email="linked-parent@example.test", school=school, password="synthetic")
    Guardian.objects.create(school_id=school.id, household=families[0],
                           account=linked, first_name="Linked", last_name="Guardian")
    unlinked = UserAccount.objects.create_user(username="other-parent", email="other-parent@example.test", school=school, password="synthetic")
    client = APIClient()
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    client.force_authenticate(user=linked)
    allowed = client.get(f"/api/v1/summer-camp/parent/{children[0].id}/")
    assert allowed.status_code == 200 and allowed.data["student_id"] == str(children[0].id)
    assert len(allowed.data["rows"]) == 1 and allowed.data["rows"][0]["enrollment_id"] is not None
    denied = client.get(f"/api/v1/summer-camp/parent/{children[1].id}/")
    assert denied.status_code == 403 and denied.data == {"detail": "Forbidden"}
    client.force_authenticate(user=unlinked)
    assert client.get(f"/api/v1/summer-camp/parent/{children[0].id}/").status_code == 403
    assert SummerCampEnrollment.objects.filter(school=school).count() == 2
