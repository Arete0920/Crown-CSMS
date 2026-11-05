"""Fail-closed payer association and school finance grants on registered legacy APIs.

Only synthetic schools/users; no real payment activation or customer records.
"""
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import (
    CrownPermission, Family, Guardian, RolePermission, School,
    UserAccount, UserRole,
)
from finance.models import FinanceInvoice, FinanceObligation, ObligationType
from households.models import Guardian as HouseholdGuardian, Household


class FinancePayerAuthorityTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Finance Authority School A")
        self.foreign = School.objects.create(name="Finance Authority School B")
        self.staff = UserAccount.objects.create_user(
            username="finance-writer-synthetic", email="writer@school-a.invalid",
            password="test-only", is_staff=True, school=self.school,
        )
        self.payer = UserAccount.objects.create_user(
            username="payer-synthetic", email="payer@school-a.invalid",
            password="test-only", school=self.school,
        )
        self.foreign_payer = UserAccount.objects.create_user(
            username="payer-foreign", email="payer@school-b.invalid",
            password="test-only", school=self.foreign,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff)

    def grant_finance(self, *, edit=False):
        UserRole.objects.get_or_create(
            school=self.school, user=self.staff, role_code="FINANCE_DIRECTOR",
        )
        codes = ("finance.view", "finance.edit") if edit else ("finance.view",)
        for code in codes:
            permission, _ = CrownPermission.objects.get_or_create(code=code)
            RolePermission.objects.get_or_create(
                role_code="FINANCE_DIRECTOR", permission=permission,
            )

    def grant_parent(self, payer, school=None):
        UserRole.objects.get_or_create(
            school=school or self.school, user=payer, role_code="PARENT",
        )

    def post(self, path, body, school=None):
        return self.client.post(
            path, body, format="json",
            HTTP_X_SCHOOL_ID=str((school or self.school).id),
        )

    def obligation_body(self, payer):
        return {
            "payer_user_id": str(payer.pk),
            "obligation_type": ObligationType.TUITION,
            "description": "Synthetic school tuition",
            "due_date": "2026-12-01",
            "amount_cents": 4500,
        }

    def invoice_body(self, payer, obligation_ids):
        return {
            "payer_user_id": str(payer.pk),
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "due_date": "2026-12-01",
            "obligation_ids": obligation_ids,
        }

    def make_obligation(self, payer):
        return FinanceObligation.objects.create(
            school=self.school, payer_user=payer,
            obligation_type=ObligationType.TUITION,
            description="Synthetic existing obligation",
            due_date=date(2026, 12, 1), amount_cents=4500,
        )

    def test_is_staff_alone_is_not_finance_authority(self):
        response = self.post("/api/finance/obligations/", self.obligation_body(self.payer))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(FinanceObligation.objects.exists())
        self.assertEqual(
            self.post("/api/finance/invoices/create-from-obligations/",
                      self.invoice_body(self.payer, [1])).status_code, 403,
        )
        self.assertFalse(FinanceInvoice.objects.exists())

    def test_view_grant_does_not_allow_financial_mutation(self):
        self.grant_finance()
        self.grant_parent(self.payer)
        self.assertEqual(self.client.get(
            "/api/finance/obligations/",
            HTTP_X_SCHOOL_ID=str(self.school.pk),
        ).status_code, 200)
        self.assertEqual(
            self.post("/api/finance/obligations/",
                      self.obligation_body(self.payer)).status_code, 403,
        )
        self.assertEqual(
            self.post("/api/finance/invoices/create-from-obligations/",
                      self.invoice_body(self.payer, [1])).status_code, 403,
        )
        self.assertFalse(FinanceObligation.objects.exists())

    def test_foreign_payer_denied_without_financial_side_effect(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.foreign_payer, self.foreign)
        response = self.post(
            "/api/finance/obligations/", self.obligation_body(self.foreign_payer),
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(FinanceObligation.objects.exists())

    def test_same_school_account_alone_does_not_establish_payer(self):
        self.grant_finance(edit=True)
        response = self.post(
            "/api/finance/obligations/", self.obligation_body(self.payer),
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(FinanceObligation.objects.exists())

    def test_explicit_parent_role_allows_own_school_obligation(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.payer)
        response = self.post(
            "/api/finance/obligations/", self.obligation_body(self.payer),
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(FinanceObligation.objects.filter(
            school=self.school, payer_user=self.payer,
        ).exists())

    def test_schoolless_multi_school_parent_membership_is_explicit(self):
        self.grant_finance(edit=True)
        payer = UserAccount.objects.create_user(
            username="multi-school-parent", email="multi-parent@invalid.example",
            password="test-only", school=None,
        )
        self.grant_parent(payer, self.foreign)
        self.assertEqual(
            self.post("/api/finance/obligations/",
                      self.obligation_body(payer)).status_code, 404,
        )
        self.grant_parent(payer)
        self.assertEqual(
            self.post("/api/finance/obligations/",
                      self.obligation_body(payer)).status_code, 201,
        )

    def test_verified_core_guardian_link_is_payer_authority(self):
        self.grant_finance(edit=True)
        family = Family.objects.create(
            school=self.school, family_name="Synthetic core guardian family",
        )
        guardian = Guardian.objects.create(
            school=self.school, family=family, first_name="Synthetic",
            last_name="Guardian", email="core-guardian@invalid.example",
            relationship="OTHER",
        )
        self.payer.guardian = guardian
        self.payer.save(update_fields=["guardian"])
        self.assertEqual(
            self.post("/api/finance/obligations/",
                      self.obligation_body(self.payer)).status_code, 201,
        )

    def test_verified_household_account_link_is_payer_authority(self):
        self.grant_finance(edit=True)
        household = Household.objects.create(
            school_id=self.school.id, name="Synthetic verified household",
        )
        HouseholdGuardian.objects.create(
            school_id=self.school.id, household=household,
            account=self.payer, email=self.payer.email,
            first_name="Verified", last_name="Payer",
        )
        self.assertEqual(
            self.post("/api/finance/obligations/",
                      self.obligation_body(self.payer)).status_code, 201,
        )

    def test_unauthorized_tenant_header_rejected(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.payer)
        response = self.post(
            "/api/finance/obligations/", self.obligation_body(self.payer),
            school=self.foreign,
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertFalse(FinanceObligation.objects.exists())

    def test_invoice_rejects_foreign_payer_even_with_valid_obligation(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.foreign_payer, self.foreign)
        obligation = self.make_obligation(self.payer)
        response = self.post(
            "/api/finance/invoices/create-from-obligations/",
            self.invoice_body(self.foreign_payer, [obligation.pk]),
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(FinanceInvoice.objects.exists())

    def test_invoice_rejects_missing_or_partial_obligation_selection(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.payer)
        obligation = self.make_obligation(self.payer)
        for selected_ids, expected in (
            ([], 400),
            ([obligation.pk, 999999999], 404),
            ([obligation.pk, obligation.pk], 400),
        ):
            with self.subTest(ids=selected_ids):
                response = self.post(
                    "/api/finance/invoices/create-from-obligations/",
                    self.invoice_body(self.payer, selected_ids),
                )
                self.assertEqual(response.status_code, expected)
                self.assertFalse(FinanceInvoice.objects.exists())

    def test_invoice_rejects_other_same_school_payer(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.payer)
        alternative = UserAccount.objects.create_user(
            username="other-parent", email="other-parent@invalid.example",
            password="test-only", school=self.school,
        )
        self.grant_parent(alternative)
        obligation = self.make_obligation(self.payer)
        response = self.post(
            "/api/finance/invoices/create-from-obligations/",
            self.invoice_body(alternative, [obligation.pk]),
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(FinanceInvoice.objects.exists())

    def test_invoice_succeeds_with_full_selected_school_population(self):
        self.grant_finance(edit=True)
        self.grant_parent(self.payer)
        obligation = self.make_obligation(self.payer)
        response = self.post(
            "/api/finance/invoices/create-from-obligations/",
            self.invoice_body(self.payer, [obligation.pk]),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FinanceInvoice.objects.count(), 1)
        self.assertEqual(FinanceInvoice.objects.get().lines.count(), 1)

    def test_schoolwide_finance_lists_need_explicit_view_grant(self):
        for path in (
            "/api/finance/obligations/", "/api/finance/invoices/",
            "/api/finance/donations/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(
                    path, HTTP_X_SCHOOL_ID=str(self.school.pk),
                ).status_code, 403)
        self.grant_finance()
        for path in (
            "/api/finance/obligations/", "/api/finance/invoices/",
            "/api/finance/donations/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(
                    path, HTTP_X_SCHOOL_ID=str(self.school.pk),
                ).status_code, 200)
