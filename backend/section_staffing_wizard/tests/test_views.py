import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from section_staffing_wizard.models import SectionStaffingWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/section-staffing-wizard/sessions/"

SECTIONS_POOL = [
    {"section_id": str(uuid.uuid4()), "section_name": "Math 101 A", "course_code": "MATH101", "grade_level": "6"},
]
ASSIGNMENTS = [
    {"section_id": SECTIONS_POOL[0]["section_id"], "teacher_id": str(uuid.uuid4()), "role": "primary"},
]


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _client(school):
    u = User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


class TestSectionStaffingWizardCreate(TestCase):
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


class TestSectionStaffingWizardConfigure(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        self.session_id = r.data["session_id"]

    def test_configure_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")
        self.assertEqual(r.data["term"], "2026-FALL")


class TestSectionStaffingWizardLoadSections(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        sid = r.data["session_id"]
        self.c.post(f"{BASE_URL}{sid}/configure/", {"term": "2026-FALL"}, format="json", **_h(self.school.id))
        self.session_id = sid

    def test_load_sections_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": SECTIONS_POOL},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["section_count"], 1)

    def test_stage_assignments_wrong_section(self):
        # load sections first
        self.c.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": SECTIONS_POOL},
            format="json",
            **_h(self.school.id),
        )
        bad_assignment = [{"section_id": str(uuid.uuid4()), "teacher_id": str(uuid.uuid4()), "role": "primary"}]
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": bad_assignment},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestSectionStaffingWizardTenantIsolation(TestCase):
    def test_cross_tenant_returns_404(self):
        school_a = _school()
        school_b = _school()
        c_a = _client(school_a)
        c_b = _client(school_b)
        r = c_a.post(BASE_URL, **_h(school_a.id))
        sid = r.data["session_id"]
        r2 = c_b.post(
            f"{BASE_URL}{sid}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)
