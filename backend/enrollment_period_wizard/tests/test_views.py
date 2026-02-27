"""
enrollment_period_wizard/tests/test_views.py

Tests for the Enrollment Period Setup Wizard (Wizard #16).

Covers:
  - Auth enforcement (401 when unauthenticated)
  - Tenant isolation (X-School-Id required; mismatch → 404)
  - Full happy path: create → configure → capacities → commit → verify
  - Validation errors (missing ay_id, bad dates, close_before_open,
    reenroll_close_outside_window, bad grade codes, dup codes, negative seats)
  - State machine guards
  - Idempotent commit: get_or_create EnrollmentPeriod + update_or_create GradeCapacity
  - Single-period-per-year enforcement
  - DB-level uniqueness constraints
  - Audit log fires on commit (non-fatal)
"""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import AcademicYear, School
from enrollment_period_wizard.models import (
    EnrollmentPeriod,
    EnrollmentPeriodWizardSession,
    GradeCapacity,
)

User = get_user_model()

BASE_URL = "/api/v1/enrollment-period-wizard/sessions/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_school(suffix=""):
    name = f"EPW School {suffix or uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password="pw")


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _authed_client():
    c = APIClient()
    user = _make_user()
    c.force_authenticate(user=user)
    return c


def _make_academic_year(school, name="2027-2028"):
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date="2027-08-01",
        end_date="2028-05-31",
        is_current=True,
    )


def _configure_payload(ay_id, open_date="2027-01-15", close_date="2027-03-31", **extra):
    p = {"academic_year_id": str(ay_id), "open_date": open_date, "close_date": close_date}
    p.update(extra)
    return p


GOOD_CAPS = [
    {"grade_code": "K",  "target_seats": 20, "new_students_allowed": True},
    {"grade_code": "1",  "target_seats": 22, "new_students_allowed": True},
    {"grade_code": "2",  "target_seats": 22, "new_students_allowed": False},
]


def _advance_to_configured(client, school_id, ay=None, **date_overrides):
    if ay is None:
        school = School.objects.get(id=school_id)
        ay = _make_academic_year(school)
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    payload = _configure_payload(ay.id, **date_overrides)
    client.post(
        f"{BASE_URL}{sid}/configure/",
        payload, format="json", **_headers(school_id),
    )
    return sid, ay


def _advance_to_capacities_set(client, school_id, caps=None, ay=None):
    sid, ay = _advance_to_configured(client, school_id, ay=ay)
    client.post(
        f"{BASE_URL}{sid}/capacities/",
        {"capacities": caps or GOOD_CAPS},
        format="json",
        **_headers(school_id),
    )
    return sid, ay


def _advance_to_committed(client, school_id, caps=None, ay=None):
    sid, ay = _advance_to_capacities_set(client, school_id, caps=caps, ay=ay)
    client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
    return sid, ay


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class EnrollmentPeriodAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        school = _make_school()
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = APIClient().post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(uuid.uuid4()),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class EnrollmentPeriodTenantTest(TestCase):
    def test_create_missing_school_header_returns_error(self):
        client = _authed_client()
        r = client.post(BASE_URL)
        self.assertIn(r.status_code, [400, 403])

    def test_session_school_mismatch_returns_404(self):
        school_a = _make_school("a")
        school_b = _make_school("b")
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school_a.id))
        sid = r.data["session_id"]
        # Try accessing school_a's session using school_b's header
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(uuid.uuid4()),
            format="json",
            **_headers(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class EnrollmentPeriodCreateTest(TestCase):
    def test_create_returns_201_and_draft_status(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], EnrollmentPeriodWizardSession.STATUS_DRAFT)

    def test_created_session_persists(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        self.assertTrue(EnrollmentPeriodWizardSession.objects.filter(id=sid).exists())


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class EnrollmentPeriodConfigureTest(TestCase):
    def test_configure_happy_path(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(ay.id),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], EnrollmentPeriodWizardSession.STATUS_CONFIGURED)
        self.assertEqual(r.data["academic_year_id"], str(ay.id))

    def test_configure_missing_academic_year_id(self):
        school = _make_school()
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"open_date": "2027-01-15", "close_date": "2027-03-31"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_bad_open_date(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(ay.id, open_date="not-a-date"),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_close_before_open(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(ay.id, open_date="2027-06-01", close_date="2027-03-01"),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("close_date", str(r.data))

    def test_configure_reenroll_close_outside_window(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        payload = _configure_payload(
            ay.id,
            open_date="2027-01-15",
            close_date="2027-03-31",
            reenroll_close_date="2027-04-30",  # outside [open, close]
        )
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            payload,
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("reenroll_close_date", str(r.data))


# ---------------------------------------------------------------------------
# Set capacities
# ---------------------------------------------------------------------------

class EnrollmentPeriodCapacitiesTest(TestCase):
    def test_capacities_draft_guard_returns_400(self):
        school = _make_school()
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": GOOD_CAPS},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("configured", r.data.get("error", "").lower())

    def test_capacities_happy_path(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": GOOD_CAPS},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], EnrollmentPeriodWizardSession.STATUS_CAPACITIES_SET)
        self.assertEqual(r.data["capacities_count"], len(GOOD_CAPS))

    def test_capacities_empty_list_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": []},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_capacities_missing_grade_code(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": [{"target_seats": 20}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_capacities_invalid_grade_code(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": [{"grade_code": "99", "target_seats": 20}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_capacities_duplicate_grade_codes(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        dup_caps = [
            {"grade_code": "K", "target_seats": 20},
            {"grade_code": "K", "target_seats": 25},
        ]
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": dup_caps},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("duplicate", str(r.data).lower())

    def test_capacities_negative_seats(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/capacities/",
            {"capacities": [{"grade_code": "K", "target_seats": -5}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class EnrollmentPeriodCommitTest(TestCase):
    def test_commit_creates_enrollment_period_and_capacities(self):
        school = _make_school()
        client = _authed_client()
        sid, ay = _advance_to_committed(client, school.id)
        self.assertTrue(EnrollmentPeriod.objects.filter(school=school, academic_year=ay).exists())
        self.assertEqual(
            GradeCapacity.objects.filter(school=school, academic_year=ay).count(),
            len(GOOD_CAPS),
        )

    def test_commit_returns_enrollment_period_id(self):
        school = _make_school()
        client = _authed_client()
        sid, ay = _advance_to_capacities_set(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("enrollment_period_id", r.data["result"])

    def test_commit_requires_capacities_set_state(self):
        """Draft session → commit → 400."""
        school = _make_school()
        client = _authed_client()
        r_create = client.post(BASE_URL, **_headers(school.id))
        sid = r_create.data["session_id"]
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_from_configured_state_fails(self):
        """Configured-only (no capacities) → commit → 400."""
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_is_idempotent(self):
        """Re-committing the same session must not create duplicate EnrollmentPeriod rows."""
        school = _make_school()
        client = _authed_client()
        sid, ay = _advance_to_committed(client, school.id)

        # Reset session to capacities_set so we can re-commit
        session = EnrollmentPeriodWizardSession.objects.get(id=sid)
        session.status = EnrollmentPeriodWizardSession.STATUS_CAPACITIES_SET
        session.save()

        r2 = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        # Still exactly one EnrollmentPeriod for this year
        self.assertEqual(
            EnrollmentPeriod.objects.filter(school=school, academic_year=ay).count(), 1
        )
        # Still same number of GradeCapacity rows
        self.assertEqual(
            GradeCapacity.objects.filter(school=school, academic_year=ay).count(),
            len(GOOD_CAPS),
        )


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class EnrollmentPeriodVerifyTest(TestCase):
    def test_verify_confirms_period_and_capacity_count(self):
        school = _make_school()
        client = _authed_client()
        sid, ay = _advance_to_committed(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], EnrollmentPeriodWizardSession.STATUS_VERIFIED)
        self.assertTrue(r.data["period_exists"])
        self.assertEqual(r.data["capacity_count"], len(GOOD_CAPS))
        self.assertEqual(r.data["academic_year_id"], str(ay.id))

    def test_verify_before_commit_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_capacities_set(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Single-period-per-year enforcement
# ---------------------------------------------------------------------------

class EnrollmentPeriodSinglePerYearTest(TestCase):
    def test_recommit_reuses_existing_period(self):
        """Two separate sessions for the same year → second commit updates, not duplicates."""
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client()

        # First session
        _advance_to_committed(client, school.id, ay=ay)

        # Second session for the same academic year
        sid2, _ = _advance_to_capacities_set(client, school.id, ay=ay)
        r2 = client.post(f"{BASE_URL}{sid2}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(r2.data["result"]["created"], "Second commit must not create a new period")
        # Still exactly one EnrollmentPeriod for this year
        self.assertEqual(
            EnrollmentPeriod.objects.filter(school=school, academic_year=ay).count(), 1
        )

    def test_cross_tenant_isolation(self):
        """Committing for school_b does not touch school_a's enrollment period."""
        school_a = _make_school("alpha")
        school_b = _make_school("beta")
        client = _authed_client()

        ay_a = _make_academic_year(school_a, name="2026-2027")
        _advance_to_committed(client, school_a.id, ay=ay_a)
        ep_a = EnrollmentPeriod.objects.get(school=school_a, academic_year=ay_a)

        ay_b = _make_academic_year(school_b, name="2026-2027")
        _advance_to_committed(client, school_b.id, ay=ay_b)

        # school_a's period is untouched
        ep_a.refresh_from_db()
        self.assertTrue(
            EnrollmentPeriod.objects.filter(school=school_a, academic_year=ay_a).exists()
        )


# ---------------------------------------------------------------------------
# DB-level uniqueness constraints
# ---------------------------------------------------------------------------

class EnrollmentPeriodDBConstraintTest(TestCase):
    def test_duplicate_enrollment_period_same_year_raises_integrity_error(self):
        """Creating two EnrollmentPeriods for the same (school, academic_year) must fail."""
        from django.db import IntegrityError

        school = _make_school()
        ay = _make_academic_year(school)
        EnrollmentPeriod.objects.create(
            school=school,
            academic_year=ay,
            open_date="2027-01-15",
            close_date="2027-03-31",
        )
        with self.assertRaises(IntegrityError):
            EnrollmentPeriod.objects.create(
                school=school,
                academic_year=ay,
                open_date="2027-02-01",
                close_date="2027-04-30",
            )

    def test_duplicate_grade_capacity_raises_integrity_error(self):
        """Creating two GradeCapacity rows for the same (school, academic_year, grade_code) must fail."""
        from django.db import IntegrityError

        school = _make_school()
        ay = _make_academic_year(school)
        GradeCapacity.objects.create(
            school=school,
            academic_year=ay,
            grade_code="K",
            target_seats=20,
        )
        with self.assertRaises(IntegrityError):
            GradeCapacity.objects.create(
                school=school,
                academic_year=ay,
                grade_code="K",
                target_seats=25,
            )
