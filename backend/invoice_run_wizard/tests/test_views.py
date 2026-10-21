import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserRole
from finance.models import FinanceInvoice, FinanceInvoiceLine, FinanceObligation, MoneyStatus
from invoice_run_wizard.models import InvoiceRunWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/invoice-run-wizard/sessions/"


def _make_school():
    return School.objects.create(name=f"IRW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school):
    user = _make_user()
    permission, _ = CrownPermission.objects.get_or_create(
        code="finance.edit", defaults={"description": "Edit school finances"},
    )
    RolePermission.objects.get_or_create(role_code="FINANCE_DIRECTOR", permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code="FINANCE_DIRECTOR")
    c = APIClient()
    c.force_authenticate(user=user)
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
    def test_non_finance_user_cannot_generate_invoices(self):
        school = _make_school()
        reader = APIClient()
        reader.force_authenticate(user=_make_user())
        result = reader.post(BASE_URL, **_headers(school.id))
        self.assertEqual(result.status_code, 403)
        self.assertFalse(InvoiceRunWizardSession.objects.filter(school=school).exists())

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
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_DRAFT)


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class InvoiceRunConfigureTest(TestCase):
    def test_configure_ok(self):
        school = _make_school()
        c = _client_for(school)
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
        c = _client_for(school)
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
        c = _client_for(school)
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
        c = _client_for(school)
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
        c = _client_for(school)
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
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED)
        self.assertEqual(r.data["obligation_count"], 2)

    def test_load_from_draft_rejected(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_load_zero_obligations_ok(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["obligation_count"], 0)


    def test_load_restricts_obligations_to_configured_due_date_period(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer, amount_cents=100000)
        outside = _make_obligation(school, payer, amount_cents=50000)
        outside.due_date = date(2027, 1, 1)
        outside.save(update_fields=["due_date"])
        client = _client_for(school)
        sid = _advance_to_loaded(client, school.id)
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        self.assertEqual(len(session.obligation_ids), 1)
        self.assertNotIn(str(outside.id), session.obligation_ids)

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
        c = _client_for(school)
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
        c = _client_for(school)
        sid = _advance_to_loaded(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/commit/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_is_idempotent(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id)
        r2 = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], InvoiceRunWizardSession.STATUS_COMMITTED)


    def test_recommit_preserves_original_result_and_does_not_rewrite_finances(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer, amount_cents=95000)
        client = _client_for(school)
        sid = _advance_to_loaded(client, school.id)
        url = f"{BASE_URL}{sid}/commit/"
        first = client.post(url, {"confirm": True}, format="json", **_headers(school.id))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["invoices_created"], 1)
        self.assertEqual(first.data["lines_created"], 1)
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        first_updated_at = session.updated_at
        first_result = session.commit_result.copy()

        retried = client.post(url, {"confirm": True}, format="json", **_headers(school.id))
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.data, first.data)
        session.refresh_from_db()
        self.assertEqual(session.updated_at, first_updated_at)
        self.assertEqual(session.commit_result, first_result)
        self.assertEqual(FinanceInvoice.objects.filter(school=school).count(), 1)
        self.assertEqual(FinanceInvoiceLine.objects.filter(invoice__school=school).count(), 1)

    def test_new_session_updates_existing_open_invoice_totals(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer, amount_cents=100000)
        client = _client_for(school)
        sid1 = _advance_to_committed(client, school.id)
        invoice = FinanceInvoice.objects.get(school=school, payer_user=payer)
        self.assertEqual(invoice.total_cents, 100000)
        _make_obligation(school, payer, amount_cents=50000)
        sid2 = _advance_to_loaded(client, school.id)
        resp = client.post(
            f"{BASE_URL}{sid2}/commit/", {"confirm": True},
            format="json", **_headers(school.id),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["invoices_created"], 0)
        self.assertEqual(resp.data["lines_created"], 1)
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal_cents, 150000)
        self.assertEqual(invoice.total_cents, 150000)
        self.assertEqual(FinanceInvoiceLine.objects.filter(invoice=invoice).count(), 2)

    def test_new_session_rejects_finalized_invoice_without_writes(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer, amount_cents=100000)
        client = _client_for(school)
        _advance_to_committed(client, school.id)
        invoice = FinanceInvoice.objects.get(school=school, payer_user=payer)
        invoice.status = MoneyStatus.PAID
        invoice.save(update_fields=["status"])
        _make_obligation(school, payer, amount_cents=50000)
        sid = _advance_to_loaded(client, school.id)
        resp = client.post(
            f"{BASE_URL}{sid}/commit/", {"confirm": True},
            format="json", **_headers(school.id),
        )
        self.assertEqual(resp.status_code, 409)
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_cents, 100000)
        self.assertEqual(FinanceInvoiceLine.objects.filter(invoice=invoice).count(), 1)
        self.assertEqual(
            InvoiceRunWizardSession.objects.get(pk=sid).status,
            InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED,
        )

    def test_commit_rejects_obligation_paid_after_load(self):
        school = _make_school()
        payer = _make_user()
        obligation = _make_obligation(school, payer)
        client = _client_for(school)
        sid = _advance_to_loaded(client, school.id)
        obligation.status = MoneyStatus.PAID
        obligation.save(update_fields=["status"])
        response = client.post(
            f"{BASE_URL}{sid}/commit/", {"confirm": True},
            format="json", **_headers(school.id),
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(FinanceInvoice.objects.filter(school=school).exists())
        self.assertEqual(InvoiceRunWizardSession.objects.get(pk=sid).status,
                         InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED)

    def test_overlapping_run_cannot_reinvoice_same_obligation(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer)
        client = _client_for(school)
        _advance_to_committed(client, school.id)
        sid = client.post(BASE_URL, **_headers(school.id)).data["session_id"]
        configured = client.post(
            f"{BASE_URL}{sid}/configure/",
            {"period_start": "2026-09-01", "period_end": "2026-11-30",
             "due_date": "2026-10-01"},
            format="json", **_headers(school.id),
        )
        self.assertEqual(configured.status_code, 200)
        loaded = client.post(f"{BASE_URL}{sid}/load/", {}, format="json",
                             **_headers(school.id))
        self.assertEqual(loaded.data["obligation_count"], 1)
        response = client.post(f"{BASE_URL}{sid}/commit/",
                               {"confirm": True}, format="json",
                               **_headers(school.id))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(FinanceInvoice.objects.filter(school=school).count(), 1)
        self.assertEqual(FinanceInvoiceLine.objects.filter(invoice__school=school).count(), 1)

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class InvoiceRunVerifyTest(TestCase):
    def test_verify_ok(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], InvoiceRunWizardSession.STATUS_VERIFIED)
        self.assertIn("invoice_count", r.data)

    def test_verify_from_draft_rejected(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_verify_get_is_read_only_and_post_is_idempotent(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id)
        url = f"{BASE_URL}{sid}/verify/"
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        initial_updated_at = session.updated_at

        inspection = c.get(url, **_headers(school.id))
        self.assertEqual(inspection.status_code, 200)
        self.assertEqual(inspection.data["status"], InvoiceRunWizardSession.STATUS_COMMITTED)
        session.refresh_from_db()
        self.assertEqual(session.updated_at, initial_updated_at)
        self.assertEqual(session.status, InvoiceRunWizardSession.STATUS_COMMITTED)

        self.assertEqual(c.post(url, **_headers(school.id)).status_code, 200)
        session.refresh_from_db()
        updated_after_post = session.updated_at
        self.assertEqual(c.post(url, **_headers(school.id)).status_code, 200)
        self.assertEqual(c.get(url, **_headers(school.id)).status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.updated_at, updated_after_post)

    def test_foreign_school_obligation_cannot_be_invoiced_if_snapshot_tampered(self):
        school = _make_school()
        other = _make_school()
        payer = _make_user()
        foreign_obligation = _make_obligation(other, payer)
        c = _client_for(school)
        sid = _advance_to_loaded(c, school.id)
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        session.obligation_ids = [str(foreign_obligation.id)]
        session.save(update_fields=["obligation_ids"])

        denied = c.post(
            f"{BASE_URL}{sid}/commit/", {"confirm": True},
            format="json", **_headers(school.id),
        )
        self.assertEqual(denied.status_code, 409)
        self.assertFalse(FinanceInvoice.objects.filter(school=school).exists())
        session.refresh_from_db()
        self.assertEqual(session.status, InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED)

    def test_verify_is_idempotent(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id)
        c.post(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        r2 = c.post(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], InvoiceRunWizardSession.STATUS_VERIFIED)


class InvoiceRunSecurityRegressionTest(TestCase):
    def test_non_usd_obligation_is_rejected_before_any_invoice_write(self):
        school = _make_school()
        obligation = _make_obligation(school, _make_user())
        obligation.currency = "EUR"
        obligation.save(update_fields=["currency"])
        client = _client_for(school)
        sid = _advance_to_loaded(client, school.id)

        response = client.post(
            f"{BASE_URL}{sid}/commit/", {"confirm": True},
            format="json", **_headers(school.id),
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(FinanceInvoice.objects.filter(school=school).exists())
        self.assertFalse(FinanceInvoiceLine.objects.filter(invoice__school=school).exists())
        self.assertEqual(
            InvoiceRunWizardSession.objects.get(pk=sid).status,
            InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED,
        )

    def test_existing_non_usd_invoice_does_not_accept_usd_lines(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer, amount_cents=100000)
        client = _client_for(school)
        _advance_to_committed(client, school.id)
        invoice = FinanceInvoice.objects.get(school=school, payer_user=payer)
        invoice.currency = "EUR"
        invoice.save(update_fields=["currency"])
        _make_obligation(school, payer, amount_cents=50000)
        sid = _advance_to_loaded(client, school.id)

        response = client.post(
            f"{BASE_URL}{sid}/commit/", {"confirm": True},
            format="json", **_headers(school.id),
        )
        self.assertEqual(response.status_code, 409)
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_cents, 100000)
        self.assertEqual(invoice.currency, "EUR")
        self.assertEqual(FinanceInvoiceLine.objects.filter(invoice=invoice).count(), 1)
        self.assertEqual(
            InvoiceRunWizardSession.objects.get(pk=sid).status,
            InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED,
        )

    def test_mixed_and_unknown_snapshots_reject_before_any_financial_write(self):
        from finance.models import FinanceInvoiceLine
        from unittest.mock import patch

        school, other = _make_school(), _make_school()
        payer = _make_user()
        own = _make_obligation(school, payer)
        foreign = _make_obligation(other, payer)
        client = _client_for(school)
        sid = _advance_to_loaded(client, school.id)
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        for invalid in (str(foreign.id), str(foreign.id + 1000000)):
            with self.subTest(invalid=invalid):
                session.obligation_ids = [str(own.id), invalid]
                session.save(update_fields=["obligation_ids"])
                before = (session.status, session.commit_result, session.updated_at)
                with patch("invoice_run_wizard.views.FinanceInvoice.objects.get_or_create") as write:
                    response = client.post(
                        f"{BASE_URL}{sid}/commit/", {"confirm": True},
                        format="json", **_headers(school.id),
                    )
                self.assertEqual(response.status_code, 409)
                write.assert_not_called()
                self.assertFalse(FinanceInvoice.objects.exists())
                self.assertFalse(FinanceInvoiceLine.objects.exists())
                session.refresh_from_db()
                self.assertEqual((session.status, session.commit_result, session.updated_at), before)

    def test_line_write_failure_rolls_back_invoice_and_session(self):
        from django.db import IntegrityError
        from finance.models import FinanceInvoiceLine
        from unittest.mock import patch

        school = _make_school()
        _make_obligation(school, _make_user())
        client = _client_for(school)
        sid = _advance_to_loaded(client, school.id)
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        before = (session.status, session.commit_result, session.updated_at)
        with patch(
            "invoice_run_wizard.views.FinanceInvoiceLine.objects.get_or_create",
            side_effect=IntegrityError("synthetic line failure"),
        ):
            response = client.post(
                f"{BASE_URL}{sid}/commit/", {"confirm": True},
                format="json", **_headers(school.id),
            )
        self.assertEqual(response.status_code, 500)
        self.assertFalse(FinanceInvoice.objects.exists())
        self.assertFalse(FinanceInvoiceLine.objects.exists())
        session.refresh_from_db()
        self.assertEqual((session.status, session.commit_result, session.updated_at), before)

    def test_user_without_finance_authority_cannot_certify(self):
        school = _make_school()
        sid = _advance_to_committed(_client_for(school), school.id)
        session = InvoiceRunWizardSession.objects.get(pk=sid)
        before = session.updated_at
        reader = APIClient()
        reader.force_authenticate(user=_make_user())
        response = reader.post(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(response.status_code, 403)
        session.refresh_from_db()
        self.assertEqual(session.status, InvoiceRunWizardSession.STATUS_COMMITTED)
        self.assertEqual(session.updated_at, before)


    def test_committed_and_verified_invoice_run_cannot_be_reconfigured(self):
        school = _make_school()
        payer = _make_user()
        _make_obligation(school, payer)
        client = _client_for(school)
        sid = _advance_to_committed(client, school.id)
        url = f"{BASE_URL}{sid}/configure/"
        before_invoices = FinanceInvoice.objects.filter(school=school).count()
        before_lines = FinanceInvoiceLine.objects.filter(invoice__school=school).count()
        self.assertEqual((before_invoices, before_lines), (1, 1))

        for state in (InvoiceRunWizardSession.STATUS_COMMITTED, InvoiceRunWizardSession.STATUS_VERIFIED):
            if state == InvoiceRunWizardSession.STATUS_VERIFIED:
                self.assertEqual(client.post(f"{BASE_URL}{sid}/verify/", **_headers(school.id)).status_code, 200)
            session = InvoiceRunWizardSession.objects.get(pk=sid)
            self.assertEqual(session.status, state)
            original = (session.status, session.updated_at, session.commit_result,
                        session.period_start, session.period_end, session.due_date, session.obligation_ids)
            denied = client.post(
                url,
                {"period_start": "2027-01-01", "period_end": "2027-03-31", "due_date": "2027-04-01"},
                format="json", **_headers(school.id),
            )
            self.assertEqual(denied.status_code, 409)
            session.refresh_from_db()
            self.assertEqual(
                (session.status, session.updated_at, session.commit_result,
                 session.period_start, session.period_end, session.due_date, session.obligation_ids),
                original,
            )
            self.assertEqual(FinanceInvoice.objects.filter(school=school).count(), before_invoices)
            self.assertEqual(FinanceInvoiceLine.objects.filter(invoice__school=school).count(), before_lines)

class AuthenticatedTenantRegressionTest(TestCase):
    def test_bearer_cannot_use_finance_role_to_override_home_school(self):
        from rest_framework_simplejwt.tokens import AccessToken

        owned, other = _make_school(), _make_school()
        user = _make_user()
        user.school = owned
        user.save(update_fields=["school"])
        permission, _ = CrownPermission.objects.get_or_create(code="finance.edit")
        RolePermission.objects.get_or_create(role_code="FINANCE_DIRECTOR", permission=permission)
        for school in (owned, other):
            UserRole.objects.create(user=user, school=school, role_code="FINANCE_DIRECTOR")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
        denied = client.post(BASE_URL, **_headers(other.id))
        self.assertEqual(denied.status_code, 404)
        self.assertFalse(InvoiceRunWizardSession.objects.filter(school=other).exists())
        self.assertEqual(client.post(BASE_URL, **_headers(owned.id)).status_code, 201)
