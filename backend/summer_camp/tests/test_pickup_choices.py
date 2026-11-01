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

def test_pickup_choices_fail_closed_for_duplicate_and_foreign_enrollments():
    home = School.objects.create(name="Synthetic Home Camp")
    foreign = School.objects.create(name="Synthetic Foreign Camp")
    family = Household.objects.create(school_id=home.id, name="Home Family")
    child = Student.objects.create(school_id=home.id, household=family, first_name="Home", last_name="Child")
    program = SummerCampProgram.objects.create(school=home, name="Home Program")
    session = SummerCampSession.objects.create(school=home, program=program, name="Home Week", start_date=date(2026, 7, 1), end_date=date(2026, 7, 7), start_time=time(8), end_time=time(16), capacity=10)
    one = SummerCampEnrollment.objects.create(school=home, student=child, household=family, session=session, status="REGISTERED")
    user = UserAccount.objects.create_user(school=home, username="camp-dupe-test", email="camp-dupe-test@example.test", password="synthetic")
    permission, _ = CrownPermission.objects.get_or_create(code="summer_camp.edit")
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)
    UserRole.objects.create(user=user, school=home, role_code="HEAD_OF_SCHOOL")
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(home.id))
    url = f"/api/v1/summer-camp/enrollments/{one.id}/pickup-choices/"
    assert client.get(url).status_code == 200
    SummerCampEnrollment.objects.create(school=home, student=child, household=family, session=session, status="REGISTERED")
    assert client.get(url).status_code == 409
    foreign_client = APIClient()
    foreign_client.force_authenticate(user=user)
    foreign_client.credentials(HTTP_X_SCHOOL_ID=str(foreign.id))
    assert foreign_client.get(url).status_code in (403, 404)
