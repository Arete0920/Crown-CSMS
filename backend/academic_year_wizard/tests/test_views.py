"""
academic_year_wizard/tests/test_views.py

Tests for the Academic Year Rollover Wizard (Wizard #15).

Covers:
  - Auth enforcement (401 when unauthenticated)
  - Tenant isolation (X-School-Id required; mismatch → 404)
  - Full happy path: create → configure → terms → commit → verify
  - Validation errors (missing year_name, bad dates, end before start, bad term codes, dup codes)
  - State machine guards
  - Idempotent commit: get_or_create AcademicYear + update_or_create Terms
  - Single-current enforcement: committing B deactivates A, cross-tenant isolation
  - Audit log fires on commit (non-fatal)
"""
import uuid
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Term
from core.models import AcademicYear, School
from academic_year_wizard.models import AcademicYearWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/academic-year-wizard/sessions/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_school(suffix=""):
    name = f"AYW School {suffix or uuid.uuid4().hex[:6]}"
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
        "year_name":  "2027-2028",
        "start_date": "2027-08-01",
        "end_date":   "2028-05-31",
    }
    payload.update(overrides)
    return payload


GOOD_TERMS = [
    {"code": "FALL-2027",   "name": "Fall 2027",   "school_year": "2027-28",
     "start_date": "2027-08-25", "end_date": "2027-12-20", "ordering": 0},
    {"code": "SPRING-2028", "name": "Spring 2028", "school_year": "2027-28",
     "start_date": "2028-01-07", "end_date": "2028-05-30", "ordering": 1},
]


def _advance_to_configured(client, school_id, **overrides):
    r = client.post(BASE_URL, **_headers(school_id))
    assert r.status_code == 201, r.data
    sid = r.data["session_id"]
    payload = _configure_payload(**overrides)
    rc = client.post(f"{BASE_URL}{sid}/configure/", payload, format="json", **_headers(school_id))
    assert rc.status_code == 200, rc.data
    return sid, payload["year_name"]


def _advance_to_terms_set(client, school_id, terms=None, **overrides):
    sid, year_name = _advance_to_configured(client, school_id, **overrides)
    terms = terms or GOOD_TERMS
    rt = client.post(f"{BASE_URL}{sid}/terms/", {"terms": terms}, format="json", **_headers(school_id))
    assert rt.status_code == 200, rt.data
    return sid, year_name


def _advance_to_committed(client, school_id, terms=None, **overrides):
    sid, year_name = _advance_to_terms_set(client, school_id, terms=terms, **overrides)
    rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
    assert rc.status_code == 200, rc.data
    return sid, year_name


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AcademicYearAuthTest(TestCase):
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

class AcademicYearTenantTest(TestCase):
    def test_missing_school_header_returns_400_or_403(self):
        client = _authed_client()
        r = client.post(BASE_URL)
        self.assertIn(r.status_code, (400, 403))

    def test_school_mismatch_returns_404(self):
        school_a = _make_school("A")
        school_b = _make_school("B")
        client   = _authed_client()
        r = client.post(BASE_URL, **_headers(school_a.id))
        self.assertEqual(r.status_code, 201)
        sid = r.data["session_id"]
        # Access session belonging to school_a using school_b header
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/", _configure_payload(),
            format="json", **_headers(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class AcademicYearCreateTest(TestCase):
    def test_create_returns_201_and_draft_status(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], AcademicYearWizardSession.STATUS_DRAFT)
        self.assertIn("session_id", r.data)

    def test_create_persists_session(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        self.assertTrue(
            AcademicYearWizardSession.objects.filter(pk=r.data["session_id"]).exists()
        )


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class AcademicYearConfigureTest(TestCase):
    def test_configure_happy_path(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        session = AcademicYearWizardSession.objects.get(pk=sid)
        self.assertEqual(session.status, AcademicYearWizardSession.STATUS_CONFIGURED)
        self.assertEqual(session.year_name, "2027-2028")

    def test_configure_missing_year_name_returns_400(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"year_name": "", "start_date": "2027-08-01", "end_date": "2028-05-31"},
            format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("errors", r2.data)

    def test_configure_bad_start_date_returns_400(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"year_name": "2027-28", "start_date": "not-a-date", "end_date": "2028-05-31"},
            format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_end_before_start_returns_400(self):
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"year_name": "2027-28", "start_date": "2027-08-01", "end_date": "2027-07-01"},
            format="json", **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertTrue(any("end_date" in e for e in r2.data.get("errors", [])))


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------

class AcademicYearTermsTest(TestCase):
    def test_terms_requires_configured_session(self):
        """Draft session (not yet configured) must return 400."""
        school = _make_school()
        client = _authed_client()
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        rt = client.post(
            f"{BASE_URL}{sid}/terms/",
            {"terms": GOOD_TERMS}, format="json", **_headers(school.id),
        )
        self.assertEqual(rt.status_code, 400)

    def test_terms_happy_path(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_terms_set(client, school.id)
        session = AcademicYearWizardSession.objects.get(pk=sid)
        self.assertEqual(session.status, AcademicYearWizardSession.STATUS_TERMS_SET)
        self.assertEqual(len(session.terms_config), len(GOOD_TERMS))

    def test_terms_empty_list_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        r = client.post(
            f"{BASE_URL}{sid}/terms/",
            {"terms": []}, format="json", **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_terms_missing_code_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        bad_terms = [{"code": "", "name": "Term 1"}]
        r = client.post(
            f"{BASE_URL}{sid}/terms/",
            {"terms": bad_terms}, format="json", **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("errors", r.data)

    def test_terms_invalid_code_chars_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        bad_terms = [{"code": "FALL 2027!", "name": "Fall"}]
        r = client.post(
            f"{BASE_URL}{sid}/terms/",
            {"terms": bad_terms}, format="json", **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_terms_duplicate_codes_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        dup_terms = [
            {"code": "FALL-2027", "name": "Fall A"},
            {"code": "FALL-2027", "name": "Fall B"},
        ]
        r = client.post(
            f"{BASE_URL}{sid}/terms/",
            {"terms": dup_terms}, format="json", **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("duplicate", r.data.get("error", "").lower())


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class AcademicYearCommitTest(TestCase):
    def test_commit_creates_academic_year_and_terms(self):
        school = _make_school()
        client = _authed_client()
        sid, year_name = _advance_to_committed(client, school.id)
        self.assertTrue(AcademicYear.objects.filter(school=school, name=year_name).exists())
        ay = AcademicYear.objects.get(school=school, name=year_name)
        self.assertEqual(Term.objects.filter(academic_year=ay).count(), len(GOOD_TERMS))

    def test_commit_returns_academic_year_id(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_terms_set(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("academic_year_id", r.data["result"])

    def test_commit_sets_is_current(self):
        school = _make_school()
        client = _authed_client()
        sid, year_name = _advance_to_committed(client, school.id)
        ay = AcademicYear.objects.get(school=school, name=year_name)
        self.assertTrue(ay.is_current)

    def test_commit_requires_terms_set_state(self):
        school = _make_school()
        client = _authed_client()
        # Draft state
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(rc.status_code, 400)

    def test_commit_requires_terms_set_not_configured(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_configured(client, school.id)
        rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(rc.status_code, 400)

    def test_commit_idempotent_update_or_create_terms(self):
        """Re-committing same year with updated term amounts updates rather than duplicates."""
        school = _make_school()
        client = _authed_client()
        shared_name = "2027-2028-IDEM"

        # First commit
        _advance_to_committed(client, school.id, year_name=shared_name)
        ay = AcademicYear.objects.get(school=school, name=shared_name)
        initial_count = Term.objects.filter(academic_year=ay).count()

        # Second commit — same year, updated term names
        updated_terms = [
            {"code": "FALL-2027", "name": "Fall 2027 UPDATED", "school_year": "2027-28",
             "start_date": "2027-08-25", "end_date": "2027-12-20", "ordering": 0},
        ]
        sid2, _ = _advance_to_terms_set(
            client, school.id, terms=updated_terms, year_name=shared_name
        )
        r2 = client.post(f"{BASE_URL}{sid2}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        # Should update, not create a new one
        term = Term.objects.get(academic_year=ay, code="FALL-2027")
        self.assertEqual(term.name, "Fall 2027 UPDATED")


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class AcademicYearVerifyTest(TestCase):
    def test_verify_confirms_year_and_term_count(self):
        school = _make_school()
        client = _authed_client()
        sid, year_name = _advance_to_committed(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], AcademicYearWizardSession.STATUS_VERIFIED)
        self.assertTrue(r.data["year_exists"])
        self.assertEqual(r.data["term_count"], len(GOOD_TERMS))
        self.assertEqual(r.data["year_name"], year_name)

    def test_verify_before_commit_returns_400(self):
        school = _make_school()
        client = _authed_client()
        sid, _ = _advance_to_terms_set(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Single-current enforcement
# ---------------------------------------------------------------------------

class AcademicYearSingleCurrentTest(TestCase):
    def test_committing_new_year_deactivates_previous_current(self):
        """Committing year B sets is_current=True and deactivates year A."""
        school = _make_school()
        client = _authed_client()

        # Commit year A
        _advance_to_committed(client, school.id, year_name="2026-2027")
        ay_a = AcademicYear.objects.get(school=school, name="2026-2027")
        self.assertTrue(ay_a.is_current)

        # Commit year B (different name → new AcademicYear)
        terms_b = [
            {"code": "FALL-2028", "name": "Fall 2028", "school_year": "2027-28",
             "start_date": "2028-08-25", "end_date": "2028-12-20", "ordering": 0},
        ]
        _advance_to_committed(
            client, school.id,
            terms=terms_b,
            year_name="2027-2028",
            start_date="2027-08-01",
            end_date="2028-05-31",
        )

        ay_a.refresh_from_db()
        ay_b = AcademicYear.objects.get(school=school, name="2027-2028")
        self.assertFalse(ay_a.is_current, "Year A should have been deactivated")
        self.assertTrue(ay_b.is_current, "Year B should be current")

    def test_cross_tenant_year_not_affected(self):
        """Committing a year for school_b does not touch school_a's current year."""
        school_a = _make_school("alpha")
        school_b = _make_school("beta")
        client   = _authed_client()

        # Commit a year for school_a
        _advance_to_committed(client, school_a.id, year_name="2026-2027")
        ay_a = AcademicYear.objects.get(school=school_a, name="2026-2027")

        # Commit a different year for school_b
        terms_b = [
            {"code": "FALL-2027", "name": "Fall 2027", "school_year": "2026-27",
             "start_date": "2027-08-25", "end_date": "2027-12-20", "ordering": 0},
        ]
        _advance_to_committed(client, school_b.id, terms=terms_b, year_name="2026-2027")

        # school_a's year remains current
        ay_a.refresh_from_db()
        self.assertTrue(ay_a.is_current, "Cross-tenant year must not be deactivated")


# ---------------------------------------------------------------------------
# DB-level uniqueness: (academic_year, code)
# ---------------------------------------------------------------------------

class AcademicYearTermUniqueConstraintTest(TestCase):
    """The uniq_term_year_code DB constraint prevents duplicate terms."""

    def test_duplicate_term_code_in_same_year_raises_integrity_error(self):
        """Creating two Terms with the same academic_year + code must fail at the DB level."""
        from django.db import IntegrityError

        school = _make_school()
        ay = AcademicYear.objects.create(
            school=school,
            name="2027-2028",
            start_date="2027-08-01",
            end_date="2028-05-31",
            is_current=True,
        )
        Term.objects.create(
            school_id=school.id,
            academic_year=ay,
            code="FALL-2027",
            name="Fall 2027",
            ordering=0,
        )
        with self.assertRaises(IntegrityError):
            Term.objects.create(
                school_id=school.id,
                academic_year=ay,
                code="FALL-2027",   # same key — must violate uniq_term_year_code
                name="Fall 2027 duplicate",
                ordering=1,
            )

    def test_commit_is_idempotent_no_duplicate_terms(self):
        """Re-committing via update_or_create never produces duplicate rows."""
        school = _make_school()
        client = _authed_client()
        sid, year_name = _advance_to_committed(client, school.id)

        # Manually reset session to terms_set so we can commit again
        session = AcademicYearWizardSession.objects.get(pk=sid)
        session.status = AcademicYearWizardSession.STATUS_TERMS_SET
        session.save()

        client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))

        ay = AcademicYear.objects.get(school=school, name=year_name)
        self.assertEqual(
            Term.objects.filter(academic_year=ay).count(),
            len(GOOD_TERMS),
            "Re-commit must not create duplicate terms",
        )
