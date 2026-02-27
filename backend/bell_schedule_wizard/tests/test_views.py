import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from bell_schedule_wizard.models import BellScheduleWizardSession
from core.models import School

User = get_user_model()

BASE_URL = "/api/v1/bell-schedule-wizard/sessions/"


def _make_school():
    return School.objects.create(name=f"BSW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password="pw")


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for():
    c = APIClient()
    c.force_authenticate(user=_make_user())
    return c


PERIOD_PAYLOAD = [
    {"name": "1st Period", "start_time": "08:00", "end_time": "08:55"},
    {"name": "2nd Period", "start_time": "09:00", "end_time": "09:55"},
]


def _advance_to_configured(client, school_id):
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    client.post(
        f"{BASE_URL}{sid}/configure/",
        {"label": "Default Schedule", "school_year": "2026-2027"},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_periods_defined(client, school_id):
    sid = _advance_to_configured(client, school_id)
    client.post(
        f"{BASE_URL}{sid}/periods/",
        {"periods": PERIOD_PAYLOAD},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_committed(client, school_id):
    sid = _advance_to_periods_defined(client, school_id)
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

class BellScheduleAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class BellScheduleCreateTest(TestCase):
    def test_create_returns_201(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], BellScheduleWizardSession.STATUS_DRAFT)
        self.assertIn("session_id", r.data)

    def test_wrong_school_does_not_error_on_create(self):
        """Create only needs a valid school UUID in the header."""
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class BellScheduleConfigureTest(TestCase):
    def test_configure_ok(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"label": "A Schedule", "school_year": "2026-2027"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], BellScheduleWizardSession.STATUS_CONFIGURED)

    def test_configure_missing_label(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"school_year": "2026-2027"},
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
            {"label": "Bad School", "school_year": "2026-2027"},
            format="json",
            **_headers(other.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Define periods
# ---------------------------------------------------------------------------

class BellSchedulePeriodsTest(TestCase):
    def test_define_periods_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/periods/",
            {"periods": PERIOD_PAYLOAD},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], BellScheduleWizardSession.STATUS_PERIODS_DEFINED)
        self.assertEqual(r.data["period_count"], 2)

    def test_define_periods_empty_list(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/periods/",
            {"periods": []},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_periods_missing_name(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/periods/",
            {"periods": [{"start_time": "08:00", "end_time": "08:55"}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_periods_bad_time(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/periods/",
            {"periods": [{"name": "1st", "start_time": "bad", "end_time": "bad"}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_periods_from_draft_is_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/periods/",
            {"periods": PERIOD_PAYLOAD},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class BellScheduleCommitTest(TestCase):
    def test_commit_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_periods_defined(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], BellScheduleWizardSession.STATUS_COMMITTED)
        self.assertEqual(r.data["period_count"], 2)

    def test_commit_requires_confirm(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_periods_defined(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/commit/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

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
        self.assertEqual(r2.data["status"], BellScheduleWizardSession.STATUS_COMMITTED)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class BellScheduleVerifyTest(TestCase):
    def test_verify_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_committed(c, school.id)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], BellScheduleWizardSession.STATUS_VERIFIED)
        self.assertEqual(r.data["period_count"], 2)

    def test_verify_from_draft_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_verify_is_idempotent(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_committed(c, school.id)
        c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], BellScheduleWizardSession.STATUS_VERIFIED)
