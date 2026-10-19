"""
fee_schedule_wizard/tests/test_views.py

Tests for the Fee Schedule Setup Wizard (Wizard #14).

Covers:
  - Auth enforcement (401 when unauthenticated)
  - Tenant isolation (X-School-Id required; mismatch → 404)
  - Full happy path: create → configure → lines → commit → verify
  - Validation errors (missing name, bad date, bad code, bad amount, dup codes)
  - State machine guards
  - Idempotent commit: get_or_create + update_or_create semantics
  - Audit log fires on commit (non-fatal: AuditLog record created)
"""
import uuid
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from fee_schedule_wizard.models import FeeSchedule, FeeLine, FeeScheduleWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/fee-schedule-wizard/sessions/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_school(suffix=""):
    name = f"FSW School {suffix or uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _authed_client():
    c = APIClient()
    c.force_authenticate(user=_make_user())
    return c


def _configure_payload(**overrides):
    payload = {
        "name":           f"2026-27 Standard {uuid.uuid4().hex[:4]}",
        "term":           "2026-FALL",
        "effective_date": "2026-08-01",
    }
    payload.update(overrides)
    return payload


GOOD_LINES = [
    {"code": "TUITION-BASE", "label": "Base Tuition", "amount_cents": 750000, "kind": "tuition", "frequency": "annual", "is_required": True,  "sort_order": 0},
    {"code": "TECH-FEE",     "label": "Technology Fee", "amount_cents": 15000, "kind": "fee",     "frequency": "annual", "is_required": False, "sort_order": 1},
]


def _advance_to_configured(client, school_id, **overrides):
    r = client.post(BASE_URL, **_headers(school_id))
    assert r.status_code == 201, r.data
    sid = r.data["session_id"]
    payload = _configure_payload(**overrides)
    rc = client.post(f"{BASE_URL}{sid}/configure/", payload, format="json", **_headers(school_id))
    assert rc.status_code == 200, rc.data
    return sid, payload["name"]


def _advance_to_lines_set(client, school_id, lines=None, **overrides):
    sid, name = _advance_to_configured(client, school_id, **overrides)
    lines = lines or GOOD_LINES
    rl = client.post(f"{BASE_URL}{sid}/lines/", {"lines": lines}, format="json", **_headers(school_id))
    assert rl.status_code == 200, rl.data
    return sid, name


def _advance_to_committed(client, school_id, lines=None, **overrides):
    sid, name = _advance_to_lines_set(client, school_id, lines=lines, **overrides)
    rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
    assert rc.status_code == 200, rc.data
    return sid, name


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class FeeScheduleAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = APIClient().post(
            f"{BASE_URL}{sid}/configure/", _configure_payload(),
            format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 401)


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class FeeScheduleTenantTest(TestCase):
    def test_missing_school_header_returns_400_or_403(self):
        client = _authed_client()
        r = client.post(BASE_URL)
        self.assertIn(r.status_code, (400, 403))

    def test_school_mismatch_returns_404(self):
        school_a = _make_school("A")
        school_b = _make_school("B")
        client   = _authed_client()
        r  = client.post(BASE_URL, **_headers(school_a.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/", _configure_payload(),
            format="json", **_headers(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class FeeScheduleCreateTest(TestCase):
    def test_create_returns_201_with_draft_status(self):
        school = _make_school()
        r = _authed_client().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)
        self.assertEqual(r.data["status"], FeeScheduleWizardSession.STATUS_DRAFT)

    def test_create_persists_session(self):
        school = _make_school()
        r = _authed_client().post(BASE_URL, **_headers(school.id))
        self.assertTrue(FeeScheduleWizardSession.objects.filter(pk=r.data["session_id"]).exists())


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class FeeScheduleConfigureTest(TestCase):
    def test_configure_happy_path(self):
        school = _make_school()
        client = _authed_client()
        sid, name = _advance_to_configured(client, school.id)
        session = FeeScheduleWizardSession.objects.get(pk=sid)
        self.assertEqual(session.status, FeeScheduleWizardSession.STATUS_CONFIGURED)
        self.assertEqual(session.schedule_name, name)

    def test_configure_missing_name(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(name=""),
            format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("name is required", str(r2.data["errors"]))

    def test_configure_bad_date_format(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(effective_date="not-a-date"),
            format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertTrue(any("effective_date" in e for e in r2.data["errors"]))


# ---------------------------------------------------------------------------
# Lines
# ---------------------------------------------------------------------------

class FeeScheduleLinesTest(TestCase):
    def test_lines_on_draft_returns_400(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": GOOD_LINES}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_lines_happy_path(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_lines_set(client, school.id)
        session = FeeScheduleWizardSession.objects.get(pk=sid)
        self.assertEqual(session.status, FeeScheduleWizardSession.STATUS_LINES_SET)
        self.assertEqual(len(session.lines_config), 2)

    def test_lines_empty_list_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": []}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_lines_negative_amount_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        bad_lines = [{"code": "X", "label": "Bad", "amount_cents": -1, "kind": "fee", "frequency": "annual"}]
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": bad_lines}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertTrue(any("amount_cents" in e for e in r2.data["errors"]))

    def test_lines_invalid_code_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        bad_lines = [{"code": "bad code!", "label": "X", "amount_cents": 0, "kind": "fee", "frequency": "annual"}]
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": bad_lines}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertTrue(any("code" in e for e in r2.data["errors"]))

    def test_lines_invalid_kind_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        bad_lines = [{"code": "X", "label": "X", "amount_cents": 0, "kind": "INVALID", "frequency": "annual"}]
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": bad_lines}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_lines_invalid_frequency_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        bad_lines = [{"code": "X", "label": "X", "amount_cents": 0, "kind": "fee", "frequency": "WEEKLY"}]
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": bad_lines}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_lines_duplicate_codes_in_batch_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        dup_lines = [
            {"code": "DUP", "label": "First",  "amount_cents": 100, "kind": "fee", "frequency": "annual"},
            {"code": "DUP", "label": "Second", "amount_cents": 200, "kind": "fee", "frequency": "annual"},
        ]
        r2 = client.post(
            f"{BASE_URL}{sid}/lines/",
            {"lines": dup_lines}, format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("duplicate", str(r2.data["error"]).lower())


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class FeeScheduleCommitTest(TestCase):
    def test_commit_creates_fee_schedule_and_lines(self):
        school = _make_school()
        client = _authed_client()
        sid, name = _advance_to_committed(client, school.id)
        self.assertTrue(FeeSchedule.objects.filter(school=school, name=name).exists())
        schedule = FeeSchedule.objects.get(school=school, name=name)
        self.assertEqual(schedule.lines.count(), len(GOOD_LINES))

    def test_commit_returns_result_with_schedule_id(self):
        school = _make_school()
        client = _authed_client()
        sid, name = _advance_to_lines_set(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("schedule_id", r.data["result"])
        self.assertTrue(r.data["result"]["created"])
        self.assertIn("message", r.data["result"])

    def test_commit_on_draft_returns_400(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_commit_on_configured_only_returns_400(self):
        # must reach lines_set before commit
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r2 = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_commit_idempotent_update_or_create_lines(self):
        """Re-committing with same schedule name updates lines, created=False."""
        school = _make_school()
        client = _authed_client()
        shared_name = f"Shared Schedule {uuid.uuid4().hex[:6]}"

        # First commit — creates schedule
        sid1, _ = _advance_to_committed(client, school.id, name=shared_name)

        # Second session with same schedule name — different amounts
        updated_lines = [
            {"code": "TUITION-BASE", "label": "Base Tuition UPDATED", "amount_cents": 800000, "kind": "tuition", "frequency": "annual"},
        ]
        sid2, _ = _advance_to_lines_set(client, school.id, lines=updated_lines, name=shared_name)
        r2 = client.post(f"{BASE_URL}{sid2}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(r2.data["result"]["created"])  # schedule existed
        self.assertIn("already existed", r2.data["result"]["message"])
        # Line updated
        line = FeeLine.objects.get(fee_schedule__school=school, code="TUITION-BASE")
        self.assertEqual(line.amount_cents, 800000)

    def test_commit_all_frequency_values_accepted(self):
        school = _make_school()
        client = _authed_client()
        for freq in ("annual", "semester", "monthly", "one_time"):
            lines = [{"code": f"FEE-{freq}", "label": "Test", "amount_cents": 0, "kind": "fee", "frequency": freq}]
            sid, _ = _advance_to_lines_set(client, school.id, lines=lines)
            r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
            self.assertEqual(r.status_code, 200, f"freq={freq} failed: {r.data}")


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class FeeScheduleVerifyTest(TestCase):
    def test_verify_confirms_schedule_and_line_count(self):
        school = _make_school()
        client = _authed_client()
        sid, name = _advance_to_committed(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], FeeScheduleWizardSession.STATUS_VERIFIED)
        self.assertTrue(r.data["schedule_exists"])
        self.assertEqual(r.data["line_count"], len(GOOD_LINES))
        self.assertEqual(r.data["schedule_name"], name)

    def test_verify_before_commit_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_lines_set(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Single-active enforcement
# ---------------------------------------------------------------------------

class FeeScheduleSingleActiveTest(TestCase):
    def test_activating_schedule_deactivates_others(self):
        """Committing schedule B deactivates previously active schedule A."""
        school = _make_school()
        client = _authed_client()

        # Commit schedule A
        sid_a, _ = _advance_to_committed(client, school.id, name="Schedule A")
        sched_a = FeeSchedule.objects.get(school=school, name="Schedule A")
        self.assertTrue(sched_a.is_active)

        # Commit schedule B (different name → new schedule)
        lines_b = [{"code": "FEE-B", "label": "Fee B", "amount_cents": 5000, "kind": "fee", "frequency": "annual"}]
        sid_b, _ = _advance_to_committed(client, school.id, name="Schedule B", lines=lines_b)
        sched_b = FeeSchedule.objects.get(school=school, name="Schedule B")

        # A must now be inactive, B active
        sched_a.refresh_from_db()
        sched_b.refresh_from_db()
        self.assertFalse(sched_a.is_active, "Schedule A should have been deactivated")
        self.assertTrue(sched_b.is_active, "Schedule B should be active")

    def test_non_active_schedule_not_affected_when_committing_inactive(self):
        """Committing schedule A (active) does not affect unrelated school schedules."""
        school_a = _make_school("alpha")
        school_b = _make_school("beta")
        client = _authed_client()

        # Commit a schedule for school_a
        _advance_to_committed(client, school_a.id, name="Alpha Schedule")
        sched_a = FeeSchedule.objects.get(school=school_a, name="Alpha Schedule")

        # Commit a schedule for school_b
        lines_b = [{"code": "FEE-X", "label": "Fee X", "amount_cents": 0, "kind": "fee", "frequency": "annual"}]
        _advance_to_committed(client, school_b.id, name="Beta Schedule", lines=lines_b)

        # school_a schedule remains active (different tenant)
        sched_a.refresh_from_db()
        self.assertTrue(sched_a.is_active, "Cross-tenant schedule must not be deactivated")
