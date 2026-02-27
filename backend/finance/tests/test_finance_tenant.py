"""
finance/tests/test_finance_tenant.py — Tenant isolation invariants for Finance module.

Verifies:
  1. Missing X-School-Id header → fail-closed (400/403/404).
  2. Obligations are scoped to the requesting school — cross-school data never leaks.
  3. Parent balance only shows authenticated user's obligations.

Run with:
  python manage.py test finance.tests.test_finance_tenant
"""
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import AcademicYear, School, UserAccount
from finance.models import FinanceObligation, MoneyStatus, ObligationType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_school(name="School"):
    return School.objects.create(name=name)


def _make_user(username, *, is_staff=False):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
        is_staff=is_staff,
    )


def _make_obligation(school, payer, *, amount_cents=10_000, days_offset=30):
    return FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Tuition Q1",
        due_date=date.today() + timedelta(days=days_offset),
        amount_cents=amount_cents,
    )


# ---------------------------------------------------------------------------
# Tenant enforcement tests
# ---------------------------------------------------------------------------

class TestObligationsTenantEnforcement(TestCase):
    def setUp(self):
        self.school = _make_school("Acme Academy")
        self.staff = _make_user("admin_staff", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff)

    def test_missing_school_header_returns_fail_closed(self):
        """No X-School-Id header → 400 (MissingSchoolContext)."""
        r = self.client.get("/api/finance/obligations/")
        self.assertIn(r.status_code, (400, 403, 404), msg=f"Got {r.status_code}: {r.content}")

    def test_valid_school_header_returns_200(self):
        """Valid X-School-Id header → 200."""
        r = self.client.get(
            "/api/finance/obligations/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 200)

    def test_obligations_scoped_to_school(self):
        """Obligations from school2 are not visible to school1 requester."""
        school2 = _make_school("Other School")
        payer1 = _make_user("payer_s1")
        payer2 = _make_user("payer_s2")

        _make_obligation(self.school, payer1, amount_cents=1_000)
        _make_obligation(school2, payer2, amount_cents=9_999)

        r = self.client.get(
            "/api/finance/obligations/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["amount_cents"], 1_000)

    def test_non_staff_cannot_list_obligations(self):
        """Non-staff user → 403."""
        parent = _make_user("parent_nostaff")
        c = APIClient()
        c.force_authenticate(user=parent)
        r = c.get(
            "/api/finance/obligations/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 403)

    def test_unauthenticated_cannot_list_obligations(self):
        """Unauthenticated → 401 or 403 (middleware order can vary)."""
        c = APIClient()
        r = c.get(
            "/api/finance/obligations/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertIn(r.status_code, (401, 403))


class TestParentBalanceTenantScoping(TestCase):
    def setUp(self):
        self.school1 = _make_school("Alpha School")
        self.school2 = _make_school("Beta School")
        self.parent = _make_user("parent_alpha")
        self.client = APIClient()
        self.client.force_authenticate(user=self.parent)

    def test_parent_balance_only_shows_own_obligations(self):
        """Parent sees only their obligations in the requested school."""
        other_user = _make_user("other_person")
        _make_obligation(self.school1, self.parent, amount_cents=5_000)
        _make_obligation(self.school1, other_user, amount_cents=9_999)
        _make_obligation(self.school2, self.parent, amount_cents=3_000)

        r = self.client.get(
            "/api/finance/parent/balance/",
            HTTP_X_SCHOOL_ID=str(self.school1.id),
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        # Only self.parent's school1 obligation
        self.assertEqual(data["total_due_cents"], 5_000)
        self.assertEqual(data["balance_cents"], 5_000)

    def test_parent_balance_missing_header_fail_closed(self):
        """No header → 400."""
        r = self.client.get("/api/finance/parent/balance/")
        self.assertIn(r.status_code, (400, 403, 404))
