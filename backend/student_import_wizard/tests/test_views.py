import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School, Family, HouseholdFamilyLink, UserRole, CrownPermission, RolePermission
from households.models import Household
from student_import_wizard.models import StudentImportWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/student-import-wizard/sessions/"

COLUMN_MAP = {"First": "first_name", "Last": "last_name", "Number": "student_number", "Birth": "dob", "Status": "status", "Family": "family_id", "Household": "household_id"}
STAGED_ROWS = [{"First": "Alice", "Last": "Smith", "Grade": "K"}]


def _school():
    school = School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)
    family = Family.objects.create(school=school, family_name='Synthetic import family')
    household = Household.objects.create(school_id=school.id, name='Synthetic import household')
    HouseholdFamilyLink.objects.create(school=school, family=family, household_id=household.id, source='manual')
    return school


def _rows(school):
    bridge = HouseholdFamilyLink.objects.get(school=school)
    return [{'First':'Alice','Last':'Smith','Number':'SYNTHETIC-001','Birth':'2014-01-01','Status':'ACTIVE',
             'Family':str(bridge.family_id),'Household':str(bridge.household_id)}]


def _client(school):
    u = User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)
    UserRole.objects.create(user=u, school=school, role_code='REGISTRAR')
    permission, _ = CrownPermission.objects.get_or_create(code='rosters.edit')
    RolePermission.objects.get_or_create(role_code='REGISTRAR', permission=permission)
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


class TestStudentImportWizardCreate(TestCase):
    def test_create_returns_201_and_session_id(self):
        school = _school()
        c = _client(school)
        r = c.post(BASE_URL, **_h(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)

    def test_create_requires_auth(self):
        school = _school()
        r = self.client.post(BASE_URL, HTTP_X_SCHOOL_ID=str(school.id))
        self.assertEqual(r.status_code, 401)


class TestStudentImportWizardConfigure(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        self.session_id = r.data["session_id"]

    def _url(self):
        return f"{BASE_URL}{self.session_id}/configure/"

    def test_configure_ok(self):
        r = self.c.post(
            self._url(),
            {"column_map": COLUMN_MAP, "staged_rows": _rows(self.school)},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_missing_column_map(self):
        r = self.c.post(
            self._url(),
            {"staged_rows": _rows(self.school)},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestStudentImportWizardPreview(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        sid = r.data["session_id"]
        self.c.post(
            f"{BASE_URL}{sid}/configure/",
            {"column_map": COLUMN_MAP, "staged_rows": _rows(self.school)},
            format="json",
            **_h(self.school.id),
        )
        self.session_id = sid

    def test_preview_ok(self):
        r = self.c.post(f"{BASE_URL}{self.session_id}/preview/", **_h(self.school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["valid"], 1)

    def test_preview_wrong_state(self):
        school2 = _school()
        c2 = _client(school2)
        r2 = c2.post(BASE_URL, **_h(school2.id))
        sid2 = r2.data["session_id"]
        # session is still 'draft' — preview should reject
        r = c2.post(f"{BASE_URL}{sid2}/preview/", **_h(school2.id))
        self.assertEqual(r.status_code, 400)


class TestStudentImportWizardTenantIsolation(TestCase):
    def test_cross_tenant_returns_404(self):
        school_a = _school()
        school_b = _school()
        c_a = _client(school_a)
        c_b = _client(school_b)
        r = c_a.post(BASE_URL, **_h(school_a.id))
        session_id = r.data["session_id"]
        # school_b tries to configure school_a's session
        r2 = c_b.post(
            f"{BASE_URL}{session_id}/configure/",
            {"column_map": COLUMN_MAP, "staged_rows": _rows(school_b)},
            format="json",
            **_h(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)
