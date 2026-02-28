import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from attendance_codes_wizard.models import AttendanceCodesWizardSession

User = get_user_model()

BASE_URL = "/api/v1/attendance-codes-wizard/sessions/"

POLICY_CONFIG = {"school_year": "2025-2026", "applies_to_grades": ["K", "1", "2"]}
CODES_STAGED = [
    {"code": "A", "label": "Absent", "excused": False, "counts_as_absent": True, "notify_guardian": True},
    {"code": "T", "label": "Tardy", "excused": False, "counts_as_tardy": True, "counts_as_absent": False, "notify_guardian": False},
    {"code": "AE", "label": "Absent Excused", "excused": True, "counts_as_absent": True, "notify_guardian": True},
]


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _client(school):
    u = User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password="pw")
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


class TestAttendanceCodesWizardCreate(TestCase):
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


class TestAttendanceCodesWizardConfigure(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        self.session_id = r.data["session_id"]

    def test_configure_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"policy_config": POLICY_CONFIG},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_bad_payload(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"policy_config": "not-a-dict"},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestAttendanceCodesWizardStageCodes(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        sid = r.data["session_id"]
        self.c.post(
            f"{BASE_URL}{sid}/configure/",
            {"policy_config": POLICY_CONFIG},
            format="json",
            **_h(self.school.id),
        )
        self.session_id = sid

    def test_stage_codes_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_codes/",
            {"codes_staged": CODES_STAGED},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["code_count"], 3)

    def test_stage_codes_duplicate_rejected(self):
        dupes = [
            {"code": "A", "label": "Absent"},
            {"code": "A", "label": "Absent Dup"},
        ]
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_codes/",
            {"codes_staged": dupes},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_stage_codes_missing_required_field(self):
        bad = [{"code": "X"}]  # missing label
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_codes/",
            {"codes_staged": bad},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestAttendanceCodesWizardTenantIsolation(TestCase):
    def test_cross_tenant_returns_404(self):
        school_a = _school()
        school_b = _school()
        c_a = _client(school_a)
        c_b = _client(school_b)
        r = c_a.post(BASE_URL, **_h(school_a.id))
        sid = r.data["session_id"]
        r2 = c_b.post(
            f"{BASE_URL}{sid}/configure/",
            {"policy_config": POLICY_CONFIG},
            format="json",
            **_h(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)
