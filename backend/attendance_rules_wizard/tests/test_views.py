import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from attendance_codes_wizard.models import AttendanceConfiguration
from attendance_rules_wizard.models import AttendanceRulesWizardSession
from core.models import CrownPermission, RolePermission, School, UserRole

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE_URL = "/api/v1/attendance-rules-wizard/sessions/"
CODES_PAYLOAD = [
    {"code": "P", "label": "Present", "counts_absent": False},
    {"code": "A", "label": "Absent", "counts_absent": True},
    {"code": "T", "label": "Tardy", "counts_as_tardy": True},
]


def _school():
    return School.objects.create(name=f"ARW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


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


def _configured(client, school):
    response = client.post(BASE_URL, **_h(school.id))
    assert response.status_code == 201
    sid = response.data["session_id"]
    response = client.post(f"{BASE_URL}{sid}/configure/", {"label": "Default Rules", "school_year": "2026-2027"}, format="json", **_h(school.id))
    assert response.status_code == 200
    return sid


def _defined(client, school):
    sid = _configured(client, school)
    response = client.post(f"{BASE_URL}{sid}/codes/", {"codes": CODES_PAYLOAD}, format="json", **_h(school.id))
    assert response.status_code == 200
    return sid


class AttendanceRulesAuthorizationTest(TestCase):
    def test_create_requires_auth(self):
        school = _school()
        self.assertEqual(APIClient().post(BASE_URL, **_h(school.id)).status_code, 401)

    def test_create_requires_permission(self):
        school = _school()
        self.assertEqual(_client(school, role="TEACHER", grant=False).post(BASE_URL, **_h(school.id)).status_code, 403)

    def test_permission_is_school_scoped(self):
        school_a = _school()
        school_b = _school()
        self.assertEqual(_client(school_a).post(BASE_URL, **_h(school_b.id)).status_code, 404)


class AttendanceRulesFlowTest(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)

    def test_create_configure_define_commit_verify_persists_canonical_authority(self):
        sid = _defined(self.client, self.school)
        committed = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        self.assertEqual(committed.status_code, 200)
        self.assertEqual(committed.data["status"], AttendanceRulesWizardSession.STATUS_COMMITTED)
        configuration = AttendanceConfiguration.objects.get(school=self.school, school_year="2026-2027")
        self.assertEqual(str(configuration.id), committed.data["configuration_id"])
        self.assertEqual(configuration.label, "Default Rules")
        self.assertEqual(configuration.codes.filter(is_active=True).count(), 3)
        self.assertTrue(configuration.codes.get(code="A").counts_as_absent)
        verified = self.client.get(f"{BASE_URL}{sid}/verify/", **_h(self.school.id))
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["status"], AttendanceRulesWizardSession.STATUS_VERIFIED)
        self.assertEqual(verified.data["code_count"], 3)

    def test_commit_requires_confirm(self):
        sid = _defined(self.client, self.school)
        self.assertEqual(self.client.post(f"{BASE_URL}{sid}/commit/", {}, format="json", **_h(self.school.id)).status_code, 400)

    def test_commit_is_idempotent(self):
        sid = _defined(self.client, self.school)
        first = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        second = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(AttendanceConfiguration.objects.filter(school=self.school, school_year="2026-2027").count(), 1)

    def test_verify_detects_canonical_drift(self):
        sid = _defined(self.client, self.school)
        committed = self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id))
        configuration = AttendanceConfiguration.objects.get(id=committed.data["configuration_id"])
        configuration.codes.filter(code="P").update(is_active=False)
        self.assertEqual(self.client.get(f"{BASE_URL}{sid}/verify/", **_h(self.school.id)).status_code, 409)

    def test_invalid_transitions_are_rejected(self):
        created = self.client.post(BASE_URL, **_h(self.school.id))
        sid = created.data["session_id"]
        self.assertEqual(self.client.post(f"{BASE_URL}{sid}/codes/", {"codes": CODES_PAYLOAD}, format="json", **_h(self.school.id)).status_code, 400)
        self.assertEqual(self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **_h(self.school.id)).status_code, 400)
        self.assertEqual(self.client.get(f"{BASE_URL}{sid}/verify/", **_h(self.school.id)).status_code, 400)

    def test_code_validation_and_deduplication(self):
        sid = _configured(self.client, self.school)
        bad = self.client.post(f"{BASE_URL}{sid}/codes/", {"codes": [{"code": "TOOLONG12", "label": "Bad"}]}, format="json", **_h(self.school.id))
        self.assertEqual(bad.status_code, 400)
        deduped = self.client.post(f"{BASE_URL}{sid}/codes/", {"codes": [{"code": "A", "label": "First"}, {"code": "a", "label": "Second"}]}, format="json", **_h(self.school.id))
        self.assertEqual(deduped.status_code, 200)
        self.assertEqual(deduped.data["code_count"], 1)
