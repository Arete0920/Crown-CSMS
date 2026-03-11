"""
term_structure_wizard/tests/test_views.py

Tests for the Term & Marking Period Setup Wizard (#18).

Covers:
  - Auth enforcement (401 when unauthenticated)
  - Tenant isolation (X-School-Id required; mismatch → 404)
  - Full happy path: create → configure → periods → commit → verify
  - Validation: missing fields, bad structure_type, start > end, overlap, gap,
    first period not starting on ay.start_date, last period not ending on ay.end_date,
    duplicate period codes
  - State machine guards (draft/configured guards on commit)
  - Idempotent commit: update_or_create + stale period deletion
  - Term code lock: grade_scale TermWeights must be a subset of period codes
  - DB-level uniqueness constraints
"""
import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import AcademicYear, School
from term_structure_wizard.models import MarkingPeriod, TermStructure, TermStructureWizardSession

User = get_user_model()

BASE_URL = "/api/v1/term-structure-wizard/sessions/"

# Academic year: 2027-08-01 → 2028-05-31
AY_START = "2027-08-01"
AY_END   = "2028-05-31"

# Two semesters covering the full year (gaps/overlaps tested separately).
GOOD_SEMESTER_PERIODS = [
    {"code": "S1", "name": "Semester 1", "start_date": "2027-08-01", "end_date": "2027-12-20"},
    {"code": "S2", "name": "Semester 2", "start_date": "2027-12-21", "end_date": "2028-05-31"},
]

# Four quarters covering the full year.
GOOD_QUARTER_PERIODS = [
    {"code": "Q1", "name": "Quarter 1", "start_date": "2027-08-01", "end_date": "2027-09-30"},
    {"code": "Q2", "name": "Quarter 2", "start_date": "2027-10-01", "end_date": "2027-11-30"},
    {"code": "Q3", "name": "Quarter 3", "start_date": "2027-12-01", "end_date": "2028-02-29"},
    {"code": "Q4", "name": "Quarter 4", "start_date": "2028-03-01", "end_date": "2028-05-31"},
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_school(suffix=""):
    name = f"TSW School {suffix or uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password="pw")


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _authed_client():
    c = APIClient()
    c.force_authenticate(user=_make_user())
    return c


def _make_year(school, start=AY_START, end=AY_END):
    return AcademicYear.objects.create(
        school=school,
        name="2027-2028",
        start_date=start,
        end_date=end,
        is_current=True,
    )


def _create_session(client, school_id):
    r = client.post(BASE_URL, **_headers(school_id))
    assert r.status_code == 201, r.data
    return r.data


def _configure_session(client, school_id, session_id, ay_id, structure_type="SEMESTER"):
    r = client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"academic_year_id": str(ay_id), "structure_type": structure_type},
        format="json",
        **_headers(school_id),
    )
    assert r.status_code == 200, r.data
    return r.data


def _set_periods(client, school_id, session_id, periods=None):
    r = client.post(
        f"{BASE_URL}{session_id}/periods/",
        periods or GOOD_SEMESTER_PERIODS,
        format="json",
        **_headers(school_id),
    )
    assert r.status_code == 200, r.data
    return r.data


def _advance_to_configured(client, school_id, ay=None):
    """Advance to 'configured' state. Returns (session_id, ay)."""
    if ay is None:
        school = School.objects.get(pk=school_id)
        ay = _make_year(school)
    sess = _create_session(client, school_id)
    _configure_session(client, school_id, sess["session_id"], ay.id)
    return sess["session_id"], ay


def _advance_to_periods_set(client, school_id, ay=None, periods=None):
    """Advance to 'periods_set' state. Returns (session_id, ay)."""
    sid, ay = _advance_to_configured(client, school_id, ay)
    _set_periods(client, school_id, sid, periods=periods)
    return sid, ay


# ---------------------------------------------------------------------------
# 1. Auth
# ---------------------------------------------------------------------------

class TermStructureAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        c = APIClient()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        school = _make_school()
        c = APIClient()
        fake_id = uuid.uuid4()
        r = c.post(f"{BASE_URL}{fake_id}/configure/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# 2. Tenant isolation
# ---------------------------------------------------------------------------

class TermStructureTenantTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _authed_client()

    def test_missing_school_header(self):
        r = self.client.post(BASE_URL)
        self.assertIn(r.status_code, [400, 404])

    def test_school_mismatch_returns_404(self):
        other_school = _make_school("other")
        sess = _create_session(self.client, self.school.id)
        # Use wrong school_id for configure
        ay = _make_year(other_school)
        r = self.client.post(
            f"{BASE_URL}{sess['session_id']}/configure/",
            {"academic_year_id": str(ay.id), "structure_type": "SEMESTER"},
            format="json",
            **_headers(other_school.id),   # school_id matches session's school? No — session is under self.school
        )
        # Server should 404 because session was created with self.school, but header says other_school
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# 3. Create
# ---------------------------------------------------------------------------

class TermStructureCreateTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _authed_client()

    def test_create_returns_201_with_draft_status(self):
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], "draft")
        self.assertIn("session_id", r.data)

    def test_create_persists_session(self):
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        sid = r.data["session_id"]
        self.assertTrue(
            TermStructureWizardSession.objects.filter(pk=sid, school=self.school).exists()
        )


# ---------------------------------------------------------------------------
# 4. Configure
# ---------------------------------------------------------------------------

class TermStructureConfigureTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def _create(self):
        return _create_session(self.client, self.school.id)["session_id"]

    def test_configure_happy_path(self):
        sid = self._create()
        r = self.client.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_id": str(self.ay.id), "structure_type": "SEMESTER"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")
        self.assertEqual(r.data["structure_type"], "SEMESTER")

    def test_configure_missing_ay_id(self):
        sid = self._create()
        r = self.client.post(
            f"{BASE_URL}{sid}/configure/",
            {"structure_type": "SEMESTER"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_missing_structure_type(self):
        sid = self._create()
        r = self.client.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_id": str(self.ay.id)},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_bad_structure_type(self):
        sid = self._create()
        r = self.client.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_id": str(self.ay.id), "structure_type": "WEEKLY"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_ay_not_in_school(self):
        other_school = _make_school("other")
        other_ay = _make_year(other_school)
        sid = self._create()
        r = self.client.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_id": str(other_ay.id), "structure_type": "SEMESTER"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# 5. Set Periods
# ---------------------------------------------------------------------------

class TermStructurePeriodsTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def test_periods_draft_guard(self):
        """Cannot set periods before configuring."""
        sid = _create_session(self.client, self.school.id)["session_id"]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/",
            GOOD_SEMESTER_PERIODS,
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("draft", str(r.data).lower())

    def test_periods_happy_path_semester(self):
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/",
            GOOD_SEMESTER_PERIODS,
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "periods_set")
        self.assertEqual(r.data["periods_count"], 2)
        self.assertIn("S1", r.data["period_codes"])
        self.assertIn("S2", r.data["period_codes"])

    def test_periods_happy_path_quarters(self):
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/",
            GOOD_QUARTER_PERIODS,
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["periods_count"], 4)

    def test_periods_missing_code(self):
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"name": "No Code", "start_date": "2027-08-01", "end_date": "2028-05-31"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)

    def test_periods_start_gt_end(self):
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"code": "X1", "name": "Bad", "start_date": "2028-05-31", "end_date": "2027-08-01"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)

    def test_periods_overlap(self):
        """S2 starts before S1 ends."""
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"code": "S1", "name": "Semester 1", "start_date": "2027-08-01", "end_date": "2027-12-20"},
            {"code": "S2", "name": "Semester 2", "start_date": "2027-12-15", "end_date": "2028-05-31"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("overlap", str(r.data).lower())

    def test_periods_gap(self):
        """Gap of several days between S1 and S2."""
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"code": "S1", "name": "Semester 1", "start_date": "2027-08-01", "end_date": "2027-12-20"},
            {"code": "S2", "name": "Semester 2", "start_date": "2028-01-10", "end_date": "2028-05-31"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("gap", str(r.data).lower())

    def test_periods_first_not_ay_start(self):
        """First period starts after ay.start_date."""
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"code": "S1", "name": "Semester 1", "start_date": "2027-09-01", "end_date": "2027-12-20"},
            {"code": "S2", "name": "Semester 2", "start_date": "2027-12-21", "end_date": "2028-05-31"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)

    def test_periods_last_not_ay_end(self):
        """Last period ends before ay.end_date."""
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"code": "S1", "name": "Semester 1", "start_date": "2027-08-01", "end_date": "2027-12-20"},
            {"code": "S2", "name": "Semester 2", "start_date": "2027-12-21", "end_date": "2028-04-30"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)

    def test_periods_duplicate_code(self):
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        bad = [
            {"code": "S1", "name": "Semester 1", "start_date": "2027-08-01", "end_date": "2027-12-20"},
            {"code": "S1", "name": "Also S1",   "start_date": "2027-12-21", "end_date": "2028-05-31"},
        ]
        r = self.client.post(
            f"{BASE_URL}{sid}/periods/", bad, format="json", **_headers(self.school.id)
        )
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# 6. Commit
# ---------------------------------------------------------------------------

class TermStructureCommitTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def test_commit_creates_term_structure(self):
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        r = self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("term_structure_id", r.data)
        self.assertTrue(TermStructure.objects.filter(school=self.school, academic_year=self.ay).exists())

    def test_commit_creates_marking_periods(self):
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        ts = TermStructure.objects.get(school=self.school, academic_year=self.ay)
        self.assertEqual(MarkingPeriod.objects.filter(term_structure=ts).count(), 2)
        codes = set(MarkingPeriod.objects.filter(term_structure=ts).values_list("code", flat=True))
        self.assertEqual(codes, {"S1", "S2"})

    def test_commit_returns_structure_id(self):
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        r = self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("term_structure_id", r.data)
        self.assertEqual(r.data["periods_created"], 2)

    def test_commit_draft_guard(self):
        """Cannot commit from draft state."""
        sid = _create_session(self.client, self.school.id)["session_id"]
        r = self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_configured_guard(self):
        """Cannot commit from configured state (periods not yet set)."""
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        r = self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_idempotent_replaces_periods(self):
        """Re-committing with different period set deletes stale periods."""
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))

        # Create a second session and re-commit with quarters.
        sid2, _ = _advance_to_periods_set(
            self.client, self.school.id, ay=self.ay, periods=GOOD_QUARTER_PERIODS
        )
        self.client.post(f"{BASE_URL}{sid2}/commit/", **_headers(self.school.id))

        ts = TermStructure.objects.get(school=self.school, academic_year=self.ay)
        codes = set(MarkingPeriod.objects.filter(term_structure=ts).values_list("code", flat=True))
        # Old S1/S2 should be gone; Q1-Q4 should be present.
        self.assertEqual(codes, {"Q1", "Q2", "Q3", "Q4"})
        self.assertEqual(MarkingPeriod.objects.filter(term_structure=ts).count(), 4)


# ---------------------------------------------------------------------------
# 7. Verify
# ---------------------------------------------------------------------------

class TermStructureVerifyTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def test_verify_happy_path(self):
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        r = self.client.get(f"{BASE_URL}{sid}/verify/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("term_structure_id", r.data)
        self.assertEqual(r.data["period_count"], 2)
        self.assertIn("S1", r.data["period_codes"])
        self.assertEqual(r.data["status"], "verified")

    def test_verify_before_commit_returns_400(self):
        sid, _ = _advance_to_configured(self.client, self.school.id, ay=self.ay)
        r = self.client.get(f"{BASE_URL}{sid}/verify/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# 8. Single-active
# ---------------------------------------------------------------------------

class TermStructureSingleActiveTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def test_committed_structure_is_active(self):
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        ts = TermStructure.objects.get(school=self.school, academic_year=self.ay)
        self.assertTrue(ts.is_active)

    def test_cross_tenant_isolation(self):
        """Structure committed for school_A is not visible under school_B."""
        school_b = _make_school("B")
        ay_b     = _make_year(school_b)
        client_b = _authed_client()

        # Commit structure for school A.
        sid_a, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        self.client.post(f"{BASE_URL}{sid_a}/commit/", **_headers(self.school.id))

        # school_B has no structure.
        self.assertFalse(
            TermStructure.objects.filter(school=school_b, academic_year=ay_b).exists()
        )


# ---------------------------------------------------------------------------
# 9. Term code lock
# ---------------------------------------------------------------------------

class TermStructureTermCodeLockTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def _commit_session(self, periods=None):
        sid, _ = _advance_to_periods_set(
            self.client, self.school.id, ay=self.ay, periods=periods
        )
        return self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))

    def test_commit_passes_when_no_term_weights_exist(self):
        """No grade scale weights → lock check passes trivially."""
        r = self._commit_session(periods=GOOD_SEMESTER_PERIODS)
        self.assertEqual(r.status_code, 200)

    def test_commit_passes_when_weight_codes_match_periods(self):
        """grade scale has S1/S2 weights → commit with S1/S2 periods passes."""
        from grade_scale_wizard.models import GradeScale, TermWeight as GsTW
        scale = GradeScale.objects.create(
            school=self.school, academic_year=self.ay,
            name="Default", scale_type="LETTER", rounding="NEAREST", is_active=True,
        )
        GsTW.objects.create(scale=scale, term_code="S1", weight_bp=5000)
        GsTW.objects.create(scale=scale, term_code="S2", weight_bp=5000)

        r = self._commit_session(periods=GOOD_SEMESTER_PERIODS)
        self.assertEqual(r.status_code, 200)

    def test_commit_blocked_when_weight_codes_missing_from_periods(self):
        """grade scale has Q1–Q4 weights → commit with S1/S2 periods is blocked."""
        from grade_scale_wizard.models import GradeScale, TermWeight as GsTW
        scale = GradeScale.objects.create(
            school=self.school, academic_year=self.ay,
            name="Default", scale_type="LETTER", rounding="NEAREST", is_active=True,
        )
        GsTW.objects.create(scale=scale, term_code="Q1", weight_bp=2500)
        GsTW.objects.create(scale=scale, term_code="Q2", weight_bp=2500)
        GsTW.objects.create(scale=scale, term_code="Q3", weight_bp=2500)
        GsTW.objects.create(scale=scale, term_code="Q4", weight_bp=2500)

        r = self._commit_session(periods=GOOD_SEMESTER_PERIODS)
        self.assertEqual(r.status_code, 400)
        err = r.data.get("error", "")
        self.assertIn("Q1", err)  # at least one missing code named in error
        self.assertIn("term code lock", err.lower())


# ---------------------------------------------------------------------------
# 10. DB-level constraint
# ---------------------------------------------------------------------------

class TermStructureDBConstraintTest(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.ay     = _make_year(self.school)
        self.client = _authed_client()

    def test_duplicate_period_code_raises_integrity_error(self):
        """DB UniqueConstraint(term_structure, code) prevents duplicate codes."""
        from django.db import IntegrityError
        sid, _ = _advance_to_periods_set(self.client, self.school.id, ay=self.ay)
        self.client.post(f"{BASE_URL}{sid}/commit/", **_headers(self.school.id))
        ts = TermStructure.objects.get(school=self.school, academic_year=self.ay)

        with self.assertRaises(IntegrityError):
            MarkingPeriod.objects.create(
                term_structure=ts,
                code="S1",
                name="Duplicate S1",
                start_date=date(2027, 8, 1),
                end_date=date(2027, 12, 20),
                ordering=99,
            )
