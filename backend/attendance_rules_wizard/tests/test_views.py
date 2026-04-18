import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from attendance_rules_wizard.models import AttendanceRulesWizardSession
from core.models import School


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/attendance-rules-wizard/sessions/"


def _make_school():
    return School.objects.create(name=f"ARW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for():
    c = APIClient()
    c.force_authenticate(user=_make_user())
    return c


CODES_PAYLOAD = [
    {"code": "P", "label": "Present", "excused": False, "counts_absent": False},
    {"code": "A", "label": "Absent", "excused": False, "counts_absent": True},
    {"code": "T", "label": "Tardy", "excused": False, "counts_absent": False},
]


def _advance_to_configured(client, school_id):
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    client.post(
        f"{BASE_URL}{sid}/configure/",
        {"label": "Default Rules", "school_year": "2026-2027"},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_codes_defined(client, school_id):
    sid = _advance_to_configured(client, school_id)
    client.post(
        f"{BASE_URL}{sid}/codes/",
        {"codes": CODES_PAYLOAD},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_committed(client, school_id):
    sid = _advance_to_codes_defined(client, school_id)
    client.post(
        f"{BASE_URL}{sid}/commit/",
        {"confirm": True},
        format="json",
        **_headers(school_id),
    )
    return sid


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AttendanceRulesAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class AttendanceRulesCreateTest(TestCase):
    def test_create_returns_201(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], AttendanceRulesWizardSession.STATUS_DRAFT)


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class AttendanceRulesConfigureTest(TestCase):
    def test_configure_ok(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"label": "Default Rules", "school_year": "2026-2027"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], AttendanceRulesWizardSession.STATUS_CONFIGURED)

    def test_configure_missing_fields(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"label": ""},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_wrong_school_returns_404(self):
        school = _make_school()
        other = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"label": "X", "school_year": "2026-2027"},
            format="json",
            **_headers(other.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Define codes
# ---------------------------------------------------------------------------

class AttendanceRulesCodesTest(TestCase):
    def test_define_codes_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/codes/",
            {"codes": CODES_PAYLOAD},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], AttendanceRulesWizardSession.STATUS_CODES_DEFINED)
        self.assertEqual(r.data["code_count"], 3)

    def test_define_codes_deduplicates(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/codes/",
            {"codes": [
                {"code": "A", "label": "First"},
                {"code": "a", "label": "Second (overrides)"},
            ]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["code_count"], 1)

    def test_define_codes_empty_rejected(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/codes/",
            {"codes": []},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_codes_code_too_long(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/codes/",
            {"codes": [{"code": "TOOLONG12", "label": "Too Long"}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_codes_from_draft_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/codes/",
            {"codes": CODES_PAYLOAD},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class AttendanceRulesCommitTest(TestCase):
    def test_commit_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_codes_defined(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], AttendanceRulesWizardSession.STATUS_COMMITTED)
        self.assertEqual(r.data["code_count"], 3)

    def test_commit_requires_confirm(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_codes_defined(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/commit/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_is_idempotent(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_committed(c, school.id)
        r2 = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], AttendanceRulesWizardSession.STATUS_COMMITTED)

    def test_commit_from_draft_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class AttendanceRulesVerifyTest(TestCase):
    def test_verify_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_committed(c, school.id)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], AttendanceRulesWizardSession.STATUS_VERIFIED)
        self.assertEqual(r.data["code_count"], 3)

    def test_verify_is_idempotent(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_committed(c, school.id)
        c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], AttendanceRulesWizardSession.STATUS_VERIFIED)

    def test_verify_from_draft_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)
