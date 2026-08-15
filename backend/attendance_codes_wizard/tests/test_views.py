import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from attendance_codes_wizard.models import AttendanceCode, AttendanceConfiguration
from core.models import CrownPermission, RolePermission, School, UserRole

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE_URL = "/api/v1/attendance-codes-wizard/sessions/"
POLICY_CONFIG = {"school_year": "2025-2026", "label": "Default Policy", "applies_to_grades": ["K", "1", "2"]}
CODES_STAGED = [
    {"code": "A", "label": "Absent", "excused": False, "counts_as_absent": True, "notify_guardian": True},
    {"code": "T", "label": "Tardy", "counts_as_tardy": True},
    {"code": "AE", "label": "Absent Excused", "excused": True, "counts_as_absent": True},
]


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _client(school, role="REGISTRAR", grant=True):
    user = User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)
    UserRole.objects.create(user=user, school=school, role_code=role)
    if grant:
        permission, _ = CrownPermission.objects.get_or_create(code="attendance.configure")
        RolePermission.objects.get_or_create(role_code=role, permission=permission)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _configured_session(client, school):
    created = client.post(BASE_URL, **_h(school.id))
    assert created.status_code == 201
    sid = created.data["session_id"]
    configured = client.post(f"{BASE_URL}{sid}/configure/", {"policy_config": POLICY_CONFIG}, format="json", **_h(school.id))
    assert configured.status_code == 200
    return sid


def _staged_session(client, school):
    sid = _configured_session(client, school)
    staged = client.post(f"{BASE_URL}{sid}/stage_codes/", {"codes_staged": CODES_STAGED}, format="json", **_h(school.id))
    assert staged.status_code == 200
    return sid


class TestAttendanceCodesWizardAuthorization(TestCase):
    def test_create_requires_auth(self):
        school = _school()
        self.assertEqual(self.client.post(BASE_URL, **_h(school.id)).status_code, 401)

    def test_create_requires_attendance_configure_permission(self):
        school = _school()
        response = _client(school, role="TEACHER", grant=False).post(BASE_URL, **_h(school.id))
        self.assertEqual(response.status_code, 403)

    def test_permission_is_school_scoped(self):
        school_a = _school()
        school_b = _school()
        client = _client(school_a)
        response = client.post(BASE_URL, **_h(school_b.id))
        self.assertEqual(response.status_code, 403)


class TestAttendanceCodesWizardValidation(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)

    def test_configure_requires_school_year(self):
        created = self.client.post(BASE_URL, **_h(self.school.id))
        response = self.client.post(f"{BASE_URL}{created.data['session_id']}/configure/", {"policy_config": {}}, format="json", **_h(self.school.id))
        self.assertEqual(response.status_code, 400)

    def test_stage_rejects_duplicate_codes(self):
        sid = _configured_session(self.client, self.school)
        response = self.client.post(f"{BASE_URL}{sid}/stage_codes/", {"codes_staged": [{"code": "A", "label": "Absent"}, {"code": "a", "label": "Duplicate"}]}, format="json", **_h(self.school.id))
        self.assertEqual(response.status_code, 400)

    def test_stage_rejects_overlength_code(self):
        sid = _configured_session(self.client, self.school)
        response = self.client.post(f"{BASE_URL}{sid}/stage_codes/", {"codes_staged": [{"code": "TOOLONG12", "label": "Bad"}]}, format="json", **_h(self.school.id))
        self.assertEqual(response.status_code, 400)


class TestAttendanceCodesWizardCanonicalPersistence(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)

    def test_commit_persists_and_verify_rereads_canonical_records(self):
        sid = _staged_session(self.client, self.school)
        committed = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        self.assertEqual(committed.status_code, 200)
        configuration = AttendanceConfiguration.objects.get(school=self.school, school_year="2025-2026")
        self.assertEqual(str(configuration.id), committed.data["configuration_id"])
        self.assertEqual(configuration.label, "Default Policy")
        self.assertEqual(configuration.codes.filter(is_active=True).count(), 3)
        verified = self.client.get(f"{BASE_URL}{sid}/verify/", **_h(self.school.id))
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["status"], "verified")
        self.assertEqual(verified.data["active_code_count"], 3)

    def test_commit_is_idempotent(self):
        sid = _staged_session(self.client, self.school)
        first = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        second = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(AttendanceConfiguration.objects.filter(school=self.school, school_year="2025-2026").count(), 1)
        self.assertEqual(AttendanceCode.objects.filter(configuration__school=self.school, is_active=True).count(), 3)

    def test_verify_detects_canonical_drift(self):
        sid = _staged_session(self.client, self.school)
        committed = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        configuration = AttendanceConfiguration.objects.get(id=committed.data["configuration_id"])
        configuration.codes.filter(code="A").update(is_active=False)
        verified = self.client.get(f"{BASE_URL}{sid}/verify/", **_h(self.school.id))
        self.assertEqual(verified.status_code, 409)

    def test_second_session_updates_same_canonical_configuration(self):
        first_sid = _staged_session(self.client, self.school)
        self.client.post(f"{BASE_URL}{first_sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        second_sid = _configured_session(self.client, self.school)
        replacement = [{"code": "P", "label": "Present"}, {"code": "A", "label": "Absent", "counts_as_absent": True}]
        self.client.post(f"{BASE_URL}{second_sid}/stage_codes/", {"codes_staged": replacement}, format="json", **_h(self.school.id))
        committed = self.client.post(f"{BASE_URL}{second_sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        self.assertEqual(committed.status_code, 200)
        configuration = AttendanceConfiguration.objects.get(school=self.school, school_year="2025-2026")
        self.assertEqual(configuration.codes.filter(is_active=True).count(), 2)
        self.assertFalse(configuration.codes.get(code="T").is_active)
