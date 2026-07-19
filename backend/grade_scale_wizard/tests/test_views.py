"""
grade_scale_wizard/tests/test_views.py

Tests for the Grade Scale & Report Card Settings Wizard (#17).

Covers:
  - Auth enforcement (401 when unauthenticated)
  - Tenant isolation (X-School-Id required; mismatch → 404)
  - Full happy path: create → configure → bands → [weights] → commit → verify
  - Validation: missing fields, bad scale_type, bad band coverage (overlap/gap/first-zero/last-100)
  - Weight validation: non-10000 sum, duplicate term_codes, wrong state
  - State machine guards
  - Single-active enforcement: second commit flips prior scale inactive
  - Idempotent commit: get_or_create scale + update_or_create bands/weights
  - DB-level uniqueness constraints
"""
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import AcademicYear, School
from grade_scale_wizard.models import (

    GradeScale,
    GradeScaleBand,
    GradeScaleWizardSession,
    TermWeight,
)

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/grade-scale-wizard/sessions/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_school(suffix=""):
    name = f"GSW School {suffix or uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user(school):
    return User.objects.create_user(
        username=f"u{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
    )


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _authed_client(school):
    c = APIClient()
    user = _make_user(school)
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


# Full-coverage bands: F(0-59) D(60-69) C(70-79) B(80-89) A(90-100)
GOOD_BANDS = [
    {"label": "A", "min_pct": 90, "max_pct": 100},
    {"label": "B", "min_pct": 80, "max_pct": 89},
    {"label": "C", "min_pct": 70, "max_pct": 79},
    {"label": "D", "min_pct": 60, "max_pct": 69},
    {"label": "F", "min_pct": 0,  "max_pct": 59},
]

# Term weights summing to 10 000 bp (Q1=Q2=Q3=Q4=25%)
GOOD_WEIGHTS = [
    {"term_code": "Q1", "weight_bp": 2500},
    {"term_code": "Q2", "weight_bp": 2500},
    {"term_code": "Q3", "weight_bp": 2500},
    {"term_code": "Q4", "weight_bp": 2500},
]


def _configure_payload(ay_id, name="2027-2028 Letter Scale", scale_type="LETTER"):
    return {"academic_year_id": str(ay_id), "name": name, "scale_type": scale_type}


def _advance_to_configured(client, school_id, ay=None, **cfg_overrides):
    if ay is None:
        school = School.objects.get(pk=school_id)
        ay = _make_academic_year(school)
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    payload = _configure_payload(ay.id, **cfg_overrides)
    client.post(f"{BASE_URL}{sid}/configure/", payload, format="json", **_headers(school_id))
    return sid, ay


def _advance_to_bands_set(client, school_id, ay=None, bands=None):
    sid, ay = _advance_to_configured(client, school_id, ay=ay)
    client.post(
        f"{BASE_URL}{sid}/bands/",
        {"bands": bands or GOOD_BANDS},
        format="json",
        **_headers(school_id),
    )
    return sid, ay


def _advance_to_committed(client, school_id, ay=None, bands=None, weights=None):
    sid, ay = _advance_to_bands_set(client, school_id, ay=ay, bands=bands)
    if weights is not None:
        client.post(
            f"{BASE_URL}{sid}/weights/",
            {"weights": weights},
            format="json",
            **_headers(school_id),
        )
    client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
    return sid, ay


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class GradeScaleAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        school = _make_school()
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
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

class GradeScaleTenantTest(TestCase):
    def test_missing_school_header_returns_error(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL)
        self.assertIn(r.status_code, [400, 403])

    def test_school_mismatch_returns_404(self):
        school_a = _make_school("a")
        school_b = _make_school("b")
        client = _authed_client(school_a)
        sid = client.post(BASE_URL, **_headers(school_a.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(uuid.uuid4()),
            format="json",
            **_headers(school_b.id),
        )
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class GradeScaleCreateTest(TestCase):
    def test_create_returns_201_and_draft(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], GradeScaleWizardSession.STATUS_DRAFT)

    def test_created_session_persists(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        self.assertTrue(GradeScaleWizardSession.objects.filter(pk=sid).exists())


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class GradeScaleConfigureTest(TestCase):
    def test_configure_happy_path(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(ay.id),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradeScaleWizardSession.STATUS_CONFIGURED)
        self.assertEqual(r.data["academic_year_id"], str(ay.id))
        self.assertEqual(r.data["scale_type"], "LETTER")
        self.assertEqual(r.data["rounding"], "NEAREST")

    def test_configure_missing_name(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_id": str(ay.id), "scale_type": "LETTER"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_missing_academic_year_id(self):
        school = _make_school()
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"name": "Test Scale", "scale_type": "LETTER"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_bad_scale_type(self):
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_id": str(ay.id), "name": "Test", "scale_type": "GPA"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("scale_type", str(r.data))

    def test_configure_ay_not_in_school(self):
        school_a = _make_school("a")
        school_b = _make_school("b")
        ay_b = _make_academic_year(school_b)
        client = _authed_client(school_a)
        sid = client.post(BASE_URL, **_headers(school_a.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(ay_b.id),
            format="json",
            **_headers(school_a.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("academic_year", str(r.data).lower())


# ---------------------------------------------------------------------------
# Bands
# ---------------------------------------------------------------------------

class GradeScaleBandsTest(TestCase):
    def test_bands_draft_guard_returns_400(self):
        school = _make_school()
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": GOOD_BANDS},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("configured", r.data.get("error", "").lower())

    def test_bands_happy_path(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": GOOD_BANDS},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradeScaleWizardSession.STATUS_BANDS_SET)
        self.assertEqual(r.data["bands_count"], len(GOOD_BANDS))

    def test_bands_missing_label(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": [{"min_pct": 0, "max_pct": 100}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_bands_min_gte_max(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": [{"label": "A", "min_pct": 90, "max_pct": 80}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_bands_overlap_detected(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        # A(85-100), B(70-89): overlap at 85-89
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": [
                {"label": "A", "min_pct": 85, "max_pct": 100},
                {"label": "B", "min_pct": 70, "max_pct": 89},
                {"label": "F", "min_pct": 0,  "max_pct": 69},
            ]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("overlap", str(r.data).lower())

    def test_bands_gap_detected(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        # F(0-79), A(90-100): gap 80-89
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": [
                {"label": "A", "min_pct": 90, "max_pct": 100},
                {"label": "F", "min_pct": 0,  "max_pct": 79},
            ]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("gap", str(r.data).lower())

    def test_bands_first_not_zero(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": [
                {"label": "A", "min_pct": 50, "max_pct": 100},
            ]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("0", str(r.data))

    def test_bands_last_not_100(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/bands/",
            {"bands": [
                {"label": "A", "min_pct": 0, "max_pct": 99},
            ]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("100", str(r.data))


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

class GradeScaleWeightsTest(TestCase):
    def test_weights_happy_path(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_bands_set(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/weights/",
            {"weights": GOOD_WEIGHTS},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradeScaleWizardSession.STATUS_WEIGHTS_SET)
        self.assertEqual(r.data["total_bp"], 10000)

    def test_weights_requires_bands_set_state(self):
        """Cannot set_weights from configured state."""
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/weights/",
            {"weights": GOOD_WEIGHTS},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_weights_wrong_sum(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_bands_set(client, school.id)
        bad_weights = [
            {"term_code": "Q1", "weight_bp": 3000},
            {"term_code": "Q2", "weight_bp": 3000},
        ]
        r = client.post(
            f"{BASE_URL}{sid}/weights/",
            {"weights": bad_weights},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("10000", str(r.data))

    def test_weights_duplicate_term_code(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_bands_set(client, school.id)
        dup_weights = [
            {"term_code": "Q1", "weight_bp": 5000},
            {"term_code": "Q1", "weight_bp": 5000},
        ]
        r = client.post(
            f"{BASE_URL}{sid}/weights/",
            {"weights": dup_weights},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("duplicate", str(r.data).lower())


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class GradeScaleCommitTest(TestCase):
    def test_commit_creates_scale_and_bands(self):
        school = _make_school()
        client = _authed_client(school)
        _, ay = _advance_to_committed(client, school.id)
        self.assertTrue(GradeScale.objects.filter(school=school, academic_year=ay).exists())
        scale = GradeScale.objects.get(school=school, academic_year=ay)
        self.assertEqual(GradeScaleBand.objects.filter(scale=scale).count(), len(GOOD_BANDS))

    def test_commit_creates_weights_when_provided(self):
        school = _make_school()
        client = _authed_client(school)
        _, ay = _advance_to_committed(client, school.id, weights=GOOD_WEIGHTS)
        scale = GradeScale.objects.get(school=school, academic_year=ay)
        self.assertEqual(TermWeight.objects.filter(scale=scale).count(), len(GOOD_WEIGHTS))

    def test_commit_returns_scale_id(self):
        school = _make_school()
        client = _authed_client(school)
        sid, ay = _advance_to_bands_set(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("scale_id", r.data["result"])

    def test_commit_draft_guard(self):
        school = _make_school()
        client = _authed_client(school)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_configured_only_guard(self):
        """Configured (no bands) → commit should fail."""
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_is_idempotent(self):
        """Re-committing produces same scale row, not a duplicate."""
        school = _make_school()
        client = _authed_client(school)
        sid, ay = _advance_to_committed(client, school.id)

        # Reset session so we can re-commit
        session = GradeScaleWizardSession.objects.get(pk=sid)
        session.status = GradeScaleWizardSession.STATUS_BANDS_SET
        session.save()

        r2 = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(r2.data["result"]["created"], "Re-commit must not create a new scale")
        self.assertEqual(GradeScale.objects.filter(school=school, academic_year=ay).count(), 1)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class GradeScaleVerifyTest(TestCase):
    def test_verify_confirms_scale_and_bands(self):
        school = _make_school()
        client = _authed_client(school)
        sid, ay = _advance_to_committed(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradeScaleWizardSession.STATUS_VERIFIED)
        self.assertTrue(r.data["scale_exists"])
        self.assertEqual(r.data["band_count"], len(GOOD_BANDS))

    def test_verify_before_commit_returns_400(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_bands_set(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Single-active enforcement
# ---------------------------------------------------------------------------

class GradeScaleSingleActiveTest(TestCase):
    def test_second_commit_flips_prior_scale_inactive(self):
        """Committing a second scale for the same year deactivates the first."""
        school = _make_school()
        ay = _make_academic_year(school)
        client = _authed_client(school)

        # First scale
        _advance_to_committed(client, school.id, ay=ay)
        first = GradeScale.objects.get(school=school, academic_year=ay, name="2027-2028 Letter Scale")
        self.assertTrue(first.is_active)

        # Second scale (different name)
        sid2, _ = _advance_to_bands_set(
            client, school.id, ay=ay, bands=GOOD_BANDS,
        )
        # Rename via re-configure trick: update scale_config directly
        session2 = GradeScaleWizardSession.objects.get(pk=sid2)
        session2.scale_config["name"] = "2027-2028 Percent Override"
        session2.save()

        client.post(f"{BASE_URL}{sid2}/commit/", **_headers(school.id))

        first.refresh_from_db()
        self.assertFalse(first.is_active, "Prior active scale must be deactivated on new commit")

    def test_cross_tenant_isolation(self):
        """Committing for school_b does not affect school_a's scales."""
        school_a = _make_school("alpha")
        school_b = _make_school("beta")
        ay_a = _make_academic_year(school_a, name="2026-2027")
        ay_b = _make_academic_year(school_b, name="2026-2027")
        client_a = _authed_client(school_a)
        client_b = _authed_client(school_b)

        _advance_to_committed(client_a, school_a.id, ay=ay_a)
        _advance_to_committed(client_b, school_b.id, ay=ay_b)

        # school_a scale still exists and active
        self.assertTrue(
            GradeScale.objects.filter(school=school_a, academic_year=ay_a, is_active=True).exists()
        )


# ---------------------------------------------------------------------------
# DB-level constraints
# ---------------------------------------------------------------------------

class GradeScaleDBConstraintTest(TestCase):
    def test_duplicate_scale_name_same_school_year_raises(self):
        from django.db import IntegrityError
        school = _make_school()
        ay = _make_academic_year(school)
        GradeScale.objects.create(school=school, academic_year=ay, name="My Scale")
        with self.assertRaises(IntegrityError):
            GradeScale.objects.create(school=school, academic_year=ay, name="My Scale")

    def test_duplicate_band_label_same_scale_raises(self):
        from django.db import IntegrityError
        school = _make_school()
        ay = _make_academic_year(school)
        scale = GradeScale.objects.create(school=school, academic_year=ay, name="Test Scale")
        GradeScaleBand.objects.create(scale=scale, label="A", min_pct=90, max_pct=100, ordering=0)
        with self.assertRaises(IntegrityError):
            GradeScaleBand.objects.create(scale=scale, label="A", min_pct=80, max_pct=89, ordering=1)
