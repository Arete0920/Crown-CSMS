from datetime import date, time
import pytest
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole, CrownPermission, RolePermission
from households.models import Household, Student
from summer_camp.models import SummerCampProgram, SummerCampSession, SummerCampEnrollment, SummerCampPickupContact

pytestmark = pytest.mark.django_db

def test_pickup_choices_require_active_school_role_and_current_registration():
    school = School.objects.create(name="Synthetic Camp Pickup School")
    family = Household.objects.create(school_id=school.id, name="Synthetic Family")
    child = Student.objects.create(school_id=school.id, household=family, first_name="Synthetic", last_name="Child")
    program = SummerCampProgram.objects.create(school=school, name="Summer")
    session = SummerCampSession.objects.create(school=school, program=program, name="Week One", start_date=date(2026, 7, 1), end_date=date(2026, 7, 7), start_time=time(8), end_time=time(16), capacity=12)
    registration = SummerCampEnrollment.objects.create(school=school, student=child, household=family, session=session, status="REGISTERED")
    contact = SummerCampPickupContact.objects.create(school=school, enrollment=registration, name="Approved", relationship="Guardian", phone="private")
    SummerCampPickupContact.objects.create(school=school, enrollment=registration, name="Inactive", is_active=False)
    user = UserAccount.objects.create_user(school=school, username="camp-pickup-test", email="camp-pickup-test@example.test", password="synthetic")
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    url = f"/api/v1/summer-camp/enrollments/{registration.id}/pickup-choices/"
    assert client.get(url).status_code == 403
    permission, _ = CrownPermission.objects.get_or_create(code="summer_camp.edit")
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)
    UserRole.objects.create(user=user, school=school, role_code="HEAD_OF_SCHOOL")
    response = client.get(url)
    assert response.status_code == 200, response.data
    assert response.data["contacts"] == [{"id": contact.id, "name": "Approved", "relationship": "Guardian"}]
    assert "private" not in str(response.data)
    registration.status = "CANCELLED"
    registration.save(update_fields=["status"])
    assert client.get(url).status_code == 404
