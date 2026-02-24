from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount
from crown_api.models import Household, HouseholdMember, Invoice, Payment, Person, UserPersonLink
from crown_api.models_households import ROLE_GUARDIAN


class BillingSummaryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password="testpass",
            is_staff=False,
        )

        self.household_a = Household.objects.create(household_name="Household A")
        self.household_b = Household.objects.create(household_name="Household B")

        self.parent_person = Person.objects.create(
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
        )
        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
        HouseholdMember.objects.create(
            household=self.household_a,
            person=self.parent_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        # Household A invoices: one OPEN, one PAID
        Invoice.objects.create(
            household=self.household_a,
            invoice_number="INV-A-0001",
            amount_cents=150000,
            status=Invoice.STATUS_OPEN,
            issued_date=date(2026, 1, 1),
            due_date=date(2026, 2, 1),
        )
        Invoice.objects.create(
            household=self.household_a,
            invoice_number="INV-A-0002",
            amount_cents=150000,
            status=Invoice.STATUS_PAID,
            issued_date=date(2025, 12, 1),
            due_date=date(2026, 1, 1),
        )

        # Household B invoice (OPEN)
        Invoice.objects.create(
            household=self.household_b,
            invoice_number="INV-B-0001",
            amount_cents=200000,
            status=Invoice.STATUS_OPEN,
            issued_date=date(2026, 1, 2),
            due_date=date(2026, 2, 2),
        )

        # Household A payment
        Payment.objects.create(
            household=self.household_a,
            payment_reference="PAY-A-0001",
            amount_cents=150000,
            payment_date=date(2026, 1, 15),
        )

    def test_staff_can_get_household_billing_summary(self):
        self.client.force_authenticate(user=self.staff_user)

        resp = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertEqual(body["household_id"], str(self.household_a.id))
        self.assertEqual(body["open_balance_cents"], 150000)
        self.assertEqual(body["invoices_count_open"], 1)
        self.assertEqual(body["invoices_count_total"], 2)
        self.assertEqual(body["last_payment_date"], "2026-01-15")

    def test_parent_scoped_and_no_existence_leak(self):
        self.client.force_authenticate(user=self.parent_user)

        ok = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(ok.status_code, 200)

        no = self.client.get(f"/api/households/{self.household_b.id}/billing/summary/")
        self.assertEqual(no.status_code, 404)

    def test_unauth_403(self):
        # IsAuthenticated enforced at DRF permission layer → 403 for unauthenticated
        resp = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(resp.status_code, 403)

    def test_recent_invoices_limited_and_contains_invoice_number(self):
        self.client.force_authenticate(user=self.staff_user)

        resp = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(resp.status_code, 200)
        recent = resp.json()["recent_invoices"]

        self.assertLessEqual(len(recent), 5)
        self.assertTrue(any(row["invoice_number"] == "INV-A-0001" for row in recent))
