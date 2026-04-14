import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from guardian_household_wizard.models import GuardianHouseholdWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/guardian-household-wizard/sessions/"

HOUSEHOLD_DATA = {"name": "Smith Family", "address": {"street": "123 Main St", "city": "Dallas"}}
GUARDIAN_DATA = [{"name": "Jane Smith", "email": "jane@example.com", "custody_type": "primary", "contact_priority": 1, "receives_communications": True}]


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _client(school):
    u = User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


class TestGuardianHouseholdWizardCreate(TestCase):
    def test_create_returns_201(self):
        school = _school()
        c = _client(school)
        r = c.post(BASE_URL, **_h(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)

    def test_create_requires_auth(self):
        school = _school()
        r = self.client.post(BASE_URL, HTTP_X_SCHOOL_ID=str(school.id))
        self.assertEqual(r.status_code, 401)


class TestGuardianHouseholdWizardConfigure(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        self.session_id = r.data["session_id"]

    def _url(self):
        return f"{BASE_URL}{self.session_id}/configure/"

    def test_configure_ok(self):
        r = self.c.post(self._url(), {"household_data": HOUSEHOLD_DATA}, format="json", **_h(self.school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "household_configured")

    def test_configure_missing_name(self):
        r = self.c.post(self._url(), {"household_data": {"address": {}}}, format="json", **_h(self.school.id))
        self.assertEqual(r.status_code, 400)


class TestGuardianHouseholdWizardAddGuardians(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        sid = r.data["session_id"]
        self.c.post(f"{BASE_URL}{sid}/configure/", {"household_data": HOUSEHOLD_DATA}, format="json", **_h(self.school.id))
        self.session_id = sid

    def test_add_guardians_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/add_guardians/",
            {"guardian_data": GUARDIAN_DATA},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "guardians_added")

    def test_add_guardians_invalid_custody(self):
        bad = [{"name": "Bob", "custody_type": "invalid"}]
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/add_guardians/",
            {"guardian_data": bad},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestGuardianHouseholdWizardTenantIsolation(TestCase):
    def test_cross_tenant_returns_404(self):
        school_a = _school()
        school_b = _school()
        c_a = _client(school_a)
        c_b = _client(school_b)
        r = c_a.post(BASE_URL, **_h(school_a.id))
        sid = r.data["session_id"]
        r2 = c_b.post(
            f"{BASE_URL}{sid}/configure/",
            {"household_data": HOUSEHOLD_DATA},
            format="json",
            **_h(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)
