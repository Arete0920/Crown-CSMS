from datetime import date
import uuid
import pytest
from rest_framework.test import APIClient
from core.models import School, Student, Family, UserAccount, UserRole, CrownPermission, RolePermission
from servicehours.models import ServiceEntry

pytestmark = pytest.mark.django_db

def test_service_entry_rejects_invalid_hours():
    school = School.objects.create(name="Validation Academy")
    user = UserAccount.objects.create_user(username=f"validation-{uuid.uuid4().hex[:8]}", password="test-only", school=school)
    UserRole.objects.create(user=user, school=school, role_code="service_test_role")
    permission, _ = CrownPermission.objects.get_or_create(code="service.manage")
    RolePermission.objects.get_or_create(role_code="service_test_role", permission=permission)
    family = Family.objects.create(school=school, family_name="Validation Family")
    student = Student.objects.create(school=school, family=family, student_number="VAL-1", first_name="Test", last_name="Student", dob=date(2012,1,1), status="ACTIVE")
    client = APIClient()
    client.force_authenticate(user=user)
    for hours in ("0", "-1.00", "1000", "not-a-number"):
        response = client.post("/api/service/entries/", {"student":str(student.id), "date":date.today().isoformat(), "hours":hours}, format="json", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 400
    assert not ServiceEntry.objects.filter(student=student).exists()
    missing = client.post("/api/service/entries/", {"student":str(student.id), "hours":"1.25"}, format="json", HTTP_X_SCHOOL_ID=str(school.id))
    assert missing.status_code == 400
    valid = client.post("/api/service/entries/", {"student":str(student.id), "date":date.today().isoformat(), "hours":"1.25"}, format="json", HTTP_X_SCHOOL_ID=str(school.id))
    assert valid.status_code == 201
    assert str(ServiceEntry.objects.get(student=student).hours) == "1.25"
