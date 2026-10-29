"""School-scoped payment settlement and refund authorization regressions.

Synthetic fixtures only. These tests do not trigger a payment gateway.
"""
from datetime import date

from django.test import TestCase
from django.urls import resolve
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from finance.models import (
    FinanceAllocation, FinanceObligation, FinancePayment, FinanceRefund,
    ObligationType, PaymentStatus, Processor,
)
from finance.services import settle_payment_and_allocate
from finance import payment_compat_api
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import Allocation as LedgerAllocation
from ledger.models import Charge as LedgerCharge
from ledger.models import LedgerAccount
from ledger.models import Payment as LedgerPayment


class FinanceSettlementAuthorityTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic finance school A")
        self.foreign = School.objects.create(name="Synthetic finance school B")
        self.actor = UserAccount.objects.create_user(
            username="synthetic-finance-staff", email="staff@synthetic.invalid",
            password="test-only", school=self.school, is_staff=True,
        )
        self.payer = UserAccount.objects.create_user(
            username="synthetic-finance-payer", email="payer@synthetic.invalid",
            password="test-only", school=self.school,
        )
        household = Household.objects.create(
            school_id=self.school.pk, name="Synthetic verified household",
        )
        HouseholdGuardian.objects.create(
            school_id=self.school.pk, household=household,
            first_name="Synthetic", last_name="Guardian",
            email=self.payer.email, account=self.payer,
        )
        LedgerAccount.objects.get_or_create(school_id=self.school.pk, household=household)
        self.obligation = FinanceObligation.objects.create(
            school=self.school, payer_user=self.payer,
            obligation_type=ObligationType.TUITION,
            due_date=date(2026, 12, 1), amount_cents=10000,
            description="Synthetic tuition obligation",
        )
        self.payment = FinancePayment.objects.create(
            school=self.school, payer_user=self.payer,
            amount_cents=10000, status=PaymentStatus.PENDING,
            processor=Processor.MANUAL,
        )

    def grant(self, *, actor=None, school=None, role="FINANCE_DIRECTOR", codes=("finance.edit",)):
        actor = actor or self.actor
        school = school or self.school
        UserRole.objects.get_or_create(user=actor, school=school, role_code=role)
        for code in codes:
            permission, _ = CrownPermission.objects.get_or_create(code=code)
            RolePermission.objects.get_or_create(
                role_code=role, permission=permission,
            )

    def post_settle(self, *, actor=None, school=None):
        client = APIClient()
        client.force_authenticate(user=actor or self.actor)
        return client.post(
            f"/api/finance/payments/{self.payment.pk}/settle/",
            {"allocations": [{"obligation_id": self.obligation.pk, "amount_cents": 10000}]},
            format="json",
            HTTP_X_SCHOOL_ID=str((school or self.school).pk),
        )

    def post_refund(self, *, actor=None, school=None, amount=1000):
        client = APIClient()
        client.force_authenticate(user=actor or self.actor)
        return client.post(
            f"/api/finance/payments/{self.payment.pk}/refund/",
            {"amount_cents": amount, "processor": Processor.MANUAL},
            format="json",
            HTTP_X_SCHOOL_ID=str((school or self.school).pk),
        )

    def settle_via_service(self):
        settle_payment_and_allocate(
            payment=self.payment,
            allocations_payload=[{
                "obligation_id": self.obligation.pk, "amount_cents": 10000,
            }],
        )

    def financial_state(self):
        self.payment.refresh_from_db()
        return (
            self.payment.status,
            FinanceAllocation.objects.count(),
            FinanceRefund.objects.count(),
            LedgerPayment.objects.count(),
            LedgerCharge.objects.count(),
            LedgerAllocation.objects.count(),
        )

    def test_registered_mutation_routes_use_canonical_payment_compatibility(self):
        self.assertIs(
            resolve(f"/api/finance/payments/{self.payment.pk}/settle/").func,
            payment_compat_api.payment_settle,
        )
        self.assertIs(
            resolve(f"/api/finance/payments/{self.payment.pk}/refund/").func,
            payment_compat_api.refund_create,
        )

    def test_is_staff_without_finance_grant_cannot_settle(self):
        before = self.financial_state()
        self.assertEqual(self.post_settle().status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_is_staff_without_finance_grant_cannot_refund(self):
        self.settle_via_service()
        before = self.financial_state()
        self.assertEqual(self.post_refund().status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_view_only_grant_cannot_mutate_money(self):
        self.grant(role="FINANCE_VIEWER", codes=("finance.view",))
        before = self.financial_state()
        self.assertEqual(self.post_settle().status_code, 403)
        self.assertEqual(self.financial_state(), before)
        self.settle_via_service()
        before = self.financial_state()
        self.assertEqual(self.post_refund().status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_other_school_edit_grant_does_not_cross_tenant(self):
        self.grant(school=self.foreign)
        before = self.financial_state()
        self.assertEqual(self.post_settle().status_code, 403)
        self.assertEqual(self.financial_state(), before)
        self.settle_via_service()
        before = self.financial_state()
        self.assertEqual(self.post_refund().status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_wrong_selected_school_denies_both_operations(self):
        self.grant()
        before = self.financial_state()
        self.assertIn(self.post_settle(school=self.foreign).status_code, (403, 404))
        self.assertEqual(self.financial_state(), before)
        self.settle_via_service()
        before = self.financial_state()
        self.assertIn(self.post_refund(school=self.foreign).status_code, (403, 404))
        self.assertEqual(self.financial_state(), before)

    def test_inactive_editor_does_not_retain_write_authority(self):
        self.grant()
        self.actor.is_active = False
        self.actor.save(update_fields=["is_active"])
        before = self.financial_state()
        self.assertEqual(self.post_settle().status_code, 403)
        self.assertEqual(self.financial_state(), before)
        self.settle_via_service()
        before = self.financial_state()
        self.assertEqual(self.post_refund().status_code, 403)
        self.assertEqual(self.financial_state(), before)

    def test_school_editor_can_settle_and_refund(self):
        self.grant()
        self.assertEqual(self.post_settle().status_code, 200)
        self.assertEqual(FinanceAllocation.objects.filter(payment=self.payment).count(), 1)
        self.assertEqual(self.post_refund().status_code, 201)
        self.assertEqual(FinanceRefund.objects.filter(payment=self.payment).count(), 1)

    def test_explicit_finance_editor_without_django_staff_bit_is_authorized(self):
        editor = UserAccount.objects.create_user(
            username="synthetic-explicit-editor",
            email="editor@synthetic.invalid", password="test-only",
            school=self.school, is_staff=False,
        )
        self.grant(actor=editor)
        self.assertEqual(self.post_settle(actor=editor).status_code, 200)
        self.assertEqual(self.post_refund(actor=editor).status_code, 201)

    def test_settlement_idempotence_is_preserved(self):
        self.grant()
        self.assertEqual(self.post_settle().status_code, 200)
        self.assertEqual(self.post_settle().status_code, 200)
        self.assertEqual(FinanceAllocation.objects.filter(payment=self.payment).count(), 1)

    def test_refund_limit_is_preserved(self):
        self.grant()
        self.settle_via_service()
        before = self.financial_state()
        self.assertEqual(self.post_refund(amount=10001).status_code, 409)
        self.assertEqual(self.financial_state(), before)
