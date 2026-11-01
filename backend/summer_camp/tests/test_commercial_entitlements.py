"""DB-backed integrated Camp commercial entitlement regression."""
from datetime import timedelta
from uuid import uuid4
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole, CrownPermission, RolePermission
from subscriptions.models import SchoolModule
from summer_camp.models import SummerCampProgramConfig, SummerCampConfigWizardState, SummerCampAttendance, SummerCampProgram, SummerCampIncident
pytestmark = pytest.mark.django_db
ROOT = "/api/v1/summer-camp/"

def setup():
    school = School.objects.create(name="Camp Entitlement " + uuid4().hex[:8])
    actor = UserAccount.objects.create_user(username="camp"+uuid4().hex, school=school, password="synthetic")
    UserRole.objects.create(user=actor, school=school, role_code="HEAD_OF_SCHOOL")
    for code in ("summer_camp.view", "summer_camp.edit"):
        perm, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=perm)
    client = APIClient()
    client.force_authenticate(user=actor)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return school, actor, client

def license(school, state="active", days=30, key="little_lambs"):
    return SchoolModule.objects.create(school=school, module_key=key, status=state, expiry_date=timezone.now()+timedelta(days=days))

@pytest.mark.parametrize("state", ["active", "trial"])
def test_entitled_staff_can_read_and_write_config(state):
    school, _, client = setup()
    license(school, state)
    assert client.get(ROOT+"config/").status_code == 200
    assert client.get(ROOT+"wizard/setup/").status_code == 200
    assert client.get(ROOT+"programs/").status_code == 200
    assert client.put(ROOT+"config/", {"camp_name": "Licensed Camp"}, format="json").status_code == 200
    assert client.post(ROOT+"wizard/setup/", {"config": {"camp_name": "Licensed Wizard"}}, format="json").status_code == 200
    assert SummerCampProgramConfig.objects.get(school=school).camp_name == "Licensed Wizard"

@pytest.mark.parametrize("state,days", [
    ("absent",30), ("inactive",30), ("suspended",30), ("expired",30),
    ("active",-1), ("trial",-1),
])
def test_unlicensed_routes_deny_without_writes(state,days):
    school, _, client = setup()
    if state != "absent":
        license(school,state,days)
    reads = ["config/","wizard/setup/","programs/","sessions/","enrollments/",
             "roster/today/","incidents/","forms/missing/","health/review-queue/","board/summary/"]
    for url in reads:
        response = client.get(ROOT+url)
        assert response.status_code == 403, (state,url,response.status_code)
        assert response.data["code"] == "MODULE_NOT_ENABLED"
    writes = [("put","config/",{"camp_name":"No"}),("post","wizard/setup/",{"config":{"camp_name":"No"}}),
              ("post","programs/",{"name":"No"}),("post","sessions/",{"name":"No"}),
              ("post","enrollments/",{}),("post","attendance/checkin/",{}),
              ("post","attendance/checkout/",{}),("post","incidents/",{})]
    for method,url,payload in writes:
        response = getattr(client,method)(ROOT+url,payload,format="json")
        assert response.status_code == 403, (state,url,response.status_code)
    assert not SummerCampProgramConfig.objects.filter(school=school).exists()
    assert not SummerCampConfigWizardState.objects.filter(school=school).exists()
    assert not SummerCampProgram.objects.filter(school=school).exists()
    assert not SummerCampAttendance.objects.filter(school=school).exists()
    assert not SummerCampIncident.objects.filter(school=school).exists()

def test_foreign_school_entitlement_and_header_cannot_authorize_access():
    school, user, client = setup()
    other = School.objects.create(name="Other Camp " + uuid4().hex[:8])
    license(other)
    assert client.get(ROOT+"config/").status_code == 403
    license(school)
    client.credentials(HTTP_X_SCHOOL_ID=str(other.id))
    assert client.get(ROOT+"config/").status_code in (403,404)
    assert client.post(ROOT+"attendance/checkin/",{},format="json").status_code in (403,404)
    assert not SummerCampProgramConfig.objects.filter(school=other).exists()

def test_care_entitlements_are_not_a_diadem_camp_license():
    school, _, client = setup()
    license(school,key="before_care")
    license(school,key="after_care")
    assert client.get(ROOT+"config/").status_code == 403

def test_entitlement_does_not_grant_role_access():
    school, _, client = setup()
    license(school)
    outsider = UserAccount.objects.create_user(username="outsider"+uuid4().hex,school=school,password="synthetic",is_staff=True)
    client.force_authenticate(user=outsider)
    assert client.get(ROOT+"config/").status_code == 403
