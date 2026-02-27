"""
finance/tests/test_finance_api.py — API integration tests for Finance module endpoints.

Covers all 9 endpoints:
  GET  /api/finance/obligations/
  POST /api/finance/obligations/
  GET  /api/finance/invoices/
  POST /api/finance/invoices/create-from-obligations/
  GET  /api/finance/parent/balance/
  POST /api/finance/payments/intent/
  POST /api/finance/payments/<id>/settle/
  POST /api/finance/payments/<id>/refund/
  POST /api/finance/donations/create/
  GET  /api/finance/donations/

Run with:
  python manage.py test finance.tests.test_finance_api
"""
import json
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School, UserAccount
from finance.models import (
    FinanceAllocation,
    FinanceInvoice,
    FinanceObligation,
    FinancePayment,
    MoneyStatus,
    ObligationType,
    PaymentStatus,
    Processor,
)
from finance.services import settle_payment_and_allocate


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _school(name="Test School"):
    return School.objects.create(name=name)


def _user(username, *, is_staff=False):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
        is_staff=is_staff,
    )


def _obligation(school, payer, *, amount_cents=10_000, days=30):
    return FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Tuition",
        due_date=date.today() + timedelta(days=days),
        amount_cents=amount_cents,
    )


def _payment(school, payer, *, amount_cents=10_000, processor=Processor.MANUAL):
    return FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=amount_cents,
        status=PaymentStatus.PENDING,
        processor=processor,
    )


def _auth_client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _json_post(client, url, data, school_id):
    return client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school_id),
    )


# ---------------------------------------------------------------------------
# Obligation list + create
# ---------------------------------------------------------------------------

class TestObligationsEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.staff = _user("o_staff", is_staff=True)
        self.parent = _user("o_parent")

    def test_list_returns_only_school_obligations(self):
        other_school = _school("Other")
        _obligation(self.school, self.staff, amount_cents=1_000)
        _obligation(other_school, self.staff, amount_cents=9_999)

        c = _auth_client(self.staff)
        r = c.get("/api/finance/obligations/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["amount_cents"], 1_000)

    def test_non_staff_list_returns_403(self):
        c = _auth_client(self.parent)
        r = c.get("/api/finance/obligations/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 403)

    def test_create_obligation_returns_201(self):
        c = _auth_client(self.staff)
        body = {
            "payer_user_id": str(self.parent.id),
            "obligation_type": "tuition",
            "description": "Fall 2026 Tuition",
            "due_date": "2026-09-01",
            "amount_cents": 50_000,
        }
        r = _json_post(c, "/api/finance/obligations/", body, self.school.id)
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["amount_cents"], 50_000)
        self.assertEqual(data["status"], "open")

    def test_create_obligation_negative_amount_returns_400(self):
        c = _auth_client(self.staff)
        body = {
            "payer_user_id": str(self.parent.id),
            "obligation_type": "tuition",
            "description": "Bad",
            "due_date": "2026-09-01",
            "amount_cents": -1,
        }
        r = _json_post(c, "/api/finance/obligations/", body, self.school.id)
        self.assertEqual(r.status_code, 400)

    def test_create_obligation_missing_required_field_returns_400(self):
        c = _auth_client(self.staff)
        body = {"obligation_type": "tuition", "description": "No payer", "payer_user_id": str(self.parent.id)}
        r = _json_post(c, "/api/finance/obligations/", body, self.school.id)
        self.assertEqual(r.status_code, 400)

    def test_unauthenticated_returns_401(self):
        c = APIClient()
        r = c.get("/api/finance/obligations/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertIn(r.status_code, (401, 403))


# ---------------------------------------------------------------------------
# Invoice create
# ---------------------------------------------------------------------------

class TestInvoiceCreateEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.staff = _user("inv_staff", is_staff=True)
        self.payer = _user("inv_payer")

    def test_create_invoice_from_obligations_returns_201(self):
        ob1 = _obligation(self.school, self.payer, amount_cents=3_000)
        ob2 = _obligation(self.school, self.payer, amount_cents=7_000)

        c = _auth_client(self.staff)
        body = {
            "payer_user_id": str(self.payer.id),
            "period_start": "2026-09-01",
            "period_end": "2026-09-30",
            "due_date": "2026-09-30",
            "obligation_ids": [ob1.id, ob2.id],
        }
        r = _json_post(c, "/api/finance/invoices/create-from-obligations/", body, self.school.id)
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["total_cents"], 10_000)
        self.assertEqual(len(data["lines"]), 2)

    def test_non_staff_cannot_create_invoice(self):
        c = _auth_client(self.payer)
        body = {
            "payer_user_id": str(self.payer.id),
            "period_start": "2026-09-01",
            "period_end": "2026-09-30",
            "due_date": "2026-09-30",
            "obligation_ids": [],
        }
        r = _json_post(c, "/api/finance/invoices/create-from-obligations/", body, self.school.id)
        self.assertEqual(r.status_code, 403)

    def test_missing_due_date_returns_400(self):
        c = _auth_client(self.staff)
        body = {"payer_user_id": str(self.payer.id), "period_start": "2026-09-01", "period_end": "2026-09-30"}
        r = _json_post(c, "/api/finance/invoices/create-from-obligations/", body, self.school.id)
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Parent balance
# ---------------------------------------------------------------------------

class TestParentBalanceEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.parent = _user("bal_parent")

    def test_balance_reflects_obligations(self):
        _obligation(self.school, self.parent, amount_cents=20_000)
        c = _auth_client(self.parent)
        r = c.get("/api/finance/parent/balance/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_due_cents"], 20_000)
        self.assertEqual(data["balance_cents"], 20_000)
        self.assertEqual(data["paid_cents"], 0)

    def test_balance_deducts_allocations(self):
        ob = _obligation(self.school, self.parent, amount_cents=10_000)
        pay = _payment(self.school, self.parent, amount_cents=10_000)
        settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": 4_000}],
        )
        c = _auth_client(self.parent)
        r = c.get("/api/finance/parent/balance/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["paid_cents"], 4_000)
        self.assertEqual(data["balance_cents"], 6_000)

    def test_void_obligations_excluded(self):
        _obligation(self.school, self.parent, amount_cents=5_000)
        FinanceObligation.objects.filter(school=self.school, payer_user=self.parent).update(
            status=MoneyStatus.VOID
        )
        c = _auth_client(self.parent)
        r = c.get("/api/finance/parent/balance/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_due_cents"], 0)


# ---------------------------------------------------------------------------
# Payment intent
# ---------------------------------------------------------------------------

class TestPaymentIntentEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.parent = _user("pi_parent")

    def test_creates_pending_payment(self):
        c = _auth_client(self.parent)
        body = {"amount_cents": 5_000, "processor": "manual"}
        r = _json_post(c, "/api/finance/payments/intent/", body, self.school.id)
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["amount_cents"], 5_000)

    def test_zero_amount_returns_400(self):
        c = _auth_client(self.parent)
        body = {"amount_cents": 0}
        r = _json_post(c, "/api/finance/payments/intent/", body, self.school.id)
        self.assertEqual(r.status_code, 400)

    def test_idempotency_key_returns_same_payment(self):
        c = _auth_client(self.parent)
        body = {"amount_cents": 1_000, "idempotency_key": "idem-abc-123"}
        r1 = _json_post(c, "/api/finance/payments/intent/", body, self.school.id)
        r2 = _json_post(c, "/api/finance/payments/intent/", body, self.school.id)
        self.assertEqual(r1.json()["id"], r2.json()["id"])

    def test_unauthenticated_returns_401(self):
        c = APIClient()
        body = {"amount_cents": 5_000}
        r = _json_post(c, "/api/finance/payments/intent/", body, self.school.id)
        self.assertIn(r.status_code, (401, 403))


# ---------------------------------------------------------------------------
# Payment settle
# ---------------------------------------------------------------------------

class TestPaymentSettleEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.staff = _user("settle_staff", is_staff=True)
        self.payer = _user("settle_payer")

    def test_settle_payment_with_allocation(self):
        ob = _obligation(self.school, self.payer, amount_cents=10_000)
        pay = _payment(self.school, self.payer, amount_cents=10_000)

        c = _auth_client(self.staff)
        body = {"allocations": [{"obligation_id": ob.id, "amount_cents": 10_000}]}
        r = _json_post(c, f"/api/finance/payments/{pay.id}/settle/", body, self.school.id)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "settled")

    def test_settle_already_settled_returns_200_idempotent(self):
        ob = _obligation(self.school, self.payer, amount_cents=5_000)
        pay = _payment(self.school, self.payer, amount_cents=5_000)
        settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": 5_000}],
        )

        c = _auth_client(self.staff)
        body = {"allocations": [{"obligation_id": ob.id, "amount_cents": 5_000}]}
        r = _json_post(c, f"/api/finance/payments/{pay.id}/settle/", body, self.school.id)
        self.assertEqual(r.status_code, 200)
        # No double allocations
        self.assertEqual(FinanceAllocation.objects.filter(payment=pay).count(), 1)

    def test_settle_nonexistent_payment_returns_404(self):
        c = _auth_client(self.staff)
        body = {"allocations": []}
        r = _json_post(c, "/api/finance/payments/999999/settle/", body, self.school.id)
        self.assertEqual(r.status_code, 404)

    def test_non_staff_cannot_settle(self):
        pay = _payment(self.school, self.payer, amount_cents=1_000)
        c = _auth_client(self.payer)
        body = {"allocations": []}
        r = _json_post(c, f"/api/finance/payments/{pay.id}/settle/", body, self.school.id)
        self.assertEqual(r.status_code, 403)


# ---------------------------------------------------------------------------
# Refund endpoint
# ---------------------------------------------------------------------------

class TestRefundEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.staff = _user("ref_staff", is_staff=True)
        self.payer = _user("ref_payer")

    def _make_settled_payment(self, amount_cents=10_000):
        ob = _obligation(self.school, self.payer, amount_cents=amount_cents)
        pay = _payment(self.school, self.payer, amount_cents=amount_cents)
        settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": amount_cents}],
        )
        return pay

    def test_refund_returns_201(self):
        pay = self._make_settled_payment(10_000)
        c = _auth_client(self.staff)
        body = {"amount_cents": 5_000}
        r = _json_post(c, f"/api/finance/payments/{pay.id}/refund/", body, self.school.id)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["amount_cents"], 5_000)

    def test_over_refund_returns_409(self):
        pay = self._make_settled_payment(5_000)
        c = _auth_client(self.staff)
        body = {"amount_cents": 5_001}
        r = _json_post(c, f"/api/finance/payments/{pay.id}/refund/", body, self.school.id)
        self.assertEqual(r.status_code, 409)

    def test_non_staff_cannot_refund(self):
        pay = self._make_settled_payment(5_000)
        c = _auth_client(self.payer)
        body = {"amount_cents": 1_000}
        r = _json_post(c, f"/api/finance/payments/{pay.id}/refund/", body, self.school.id)
        self.assertEqual(r.status_code, 403)


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------

class TestDonationEndpoint(TestCase):
    def setUp(self):
        self.school = _school()
        self.donor = _user("donor_user")
        self.staff = _user("don_staff", is_staff=True)

    def test_create_donation_returns_201(self):
        c = _auth_client(self.donor)
        body = {"amount_cents": 2_500, "fund_code": "ANNUAL_FUND", "memo": "Go team"}
        r = _json_post(c, "/api/finance/donations/create/", body, self.school.id)
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["amount_cents"], 2_500)
        self.assertEqual(data["fund_code"], "ANNUAL_FUND")

    def test_create_donation_zero_amount_returns_400(self):
        c = _auth_client(self.donor)
        body = {"amount_cents": 0, "fund_code": "ANNUAL_FUND"}
        r = _json_post(c, "/api/finance/donations/create/", body, self.school.id)
        self.assertEqual(r.status_code, 400)

    def test_list_donations_staff_only(self):
        c_staff = _auth_client(self.staff)
        r = c_staff.get("/api/finance/donations/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 200)

    def test_list_donations_non_staff_returns_403(self):
        c = _auth_client(self.donor)
        r = c.get("/api/finance/donations/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 403)

    def test_recurring_donation_fields_persisted(self):
        c = _auth_client(self.donor)
        body = {
            "amount_cents": 1_000,
            "fund_code": "MONTHLY_GIFT",
            "is_recurring": True,
            "recurring_rule": "FREQ=MONTHLY;BYMONTHDAY=1",
        }
        r = _json_post(c, "/api/finance/donations/create/", body, self.school.id)
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertTrue(data["is_recurring"])
        self.assertEqual(data["recurring_rule"], "FREQ=MONTHLY;BYMONTHDAY=1")
