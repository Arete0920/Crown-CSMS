import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from finance.models import FinanceInvoice, FinanceObligation, MoneyStatus
from invoice_run_wizard.models import InvoiceRunWizardSession

User = get_user_model()

BASE_URL = "/api/v1/invoice-run-wizard/sessions/"


def _make_school():
    return School.objects.create(name=f"IRW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password="pw")


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for():
    c = APIClient()
    c.force_authenticate(user=_make_user())
    return c


def _make_obligation(school, payer_user, amount_cents=100000):
    return FinanceObligation.objects.create(
        school=school,
        payer_user=payer_user,
        obligation_type="tuition",
        description="Test tuition obligation",
        status=MoneyStatus.OPEN,
        due_date=date(2026, 9, 1),
        amount_cents=amount_cents,
        academic_year_label="2026-2027",
    )


def _advance_to_configured(client, school_id):
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    client.post(
        f"{BASE_URL}{sid}/configure/",
        {"period_start": "2026-09-01", "period_end": "2026-12-31", "due_date": "2026-10-01"},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_loaded(client, school_id):
    sid = _advance_to_configured(client, school_id)
    client.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school_id))
    return sid


def _advance_to_committed(client, school_id):
    sid = _advance_to_loaded(client, school_id)
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

class InvoiceRunAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class InvoiceRunCreateTest(TestCase):
    def test_create_returns_201(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_DRAFT)


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class InvoiceRunConfigureTest(TestCase):
    def test_configure_ok(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"period_start": "2026-09-01", "period_end": "2026-12-31", "due_date": "2026-10-01"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], InvoiceRunWizardSession.STATUS_CONFIGURED)

    def test_configure_missing_dates(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"period_start": "2026-09-01"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_invalid_date_format(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"period_start": "not-a-date", "period_end": "2026-12-31", "due_date": "2026-10-01"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_period_end_before_start_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"period_start": "2026-12-31", "period_end": "2026-09-01", "due_date": "2026-10-01"},
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
            {"period_start": "2026-09-01", "period_end": "2026-12-31", "due_date": "2026-10-01"},
            format="json",
            **_headers(other.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Load obligations
# ---------------------------------------------------------------------------

class InvoiceRunLoadTest(TestCase):
    def test_load_returns_obligation_count(self):
        school = _make_school()
        user = _make_user()
        _make_obligation(school, user)
        _make_obligation(school, user)
        c = APIClient()
        c.force_authenticate(user=user)
        sid = _advance_to_configured(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED)
        self.assertEqual(r.data["obligation_count"], 2)

    def test_load_from_draft_rejected(self):
        school = _make_school()
        c = _client_for()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_load_zero_obligations_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_configured(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["obligation_count"], 0)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class InvoiceRunCommitTest(TestCase):
    def test_commit_creates_invoices_and_lines(self):
        school = _make_school()
        user1 = _make_user()
        user2 = _make_user()
        _make_obligation(school, user1, 100000)
        _make_obligation(school, user1, 50000)
        _make_obligation(school, user2, 75000)
        c = _client_for()
        sid = _advance_to_loaded(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_COMMITTED)
        self.assertEqual(r.data["invoices_created"], 2)
        self.assertEqual(r.data["lines_created"], 3)
        inv_count = FinanceInvoice.objects.filter(school=school).count()
        self.assertEqual(inv_count, 2)

    def test_commit_requires_confirm(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_loaded(c, school.id)
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
        self.assertEqual(r2.data["status"], InvoiceRunWizardSession.STATUS_COMMITTED)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class InvoiceRunVerifyTest(TestCase):
    def test_verify_ok(self):
        school = _make_school()
        c = _client_for()
        sid = _advance_to_committed(c, school.id)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_VERIFIED)
        self.assertIn("invoice_count", r.data)

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
        self.assertEqual(r2.data["status"], InvoiceRunWizardSession.STATUS_VERIFIED)
