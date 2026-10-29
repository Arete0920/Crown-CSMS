"""Ledger household identity: no email identity, no cross-household postings.

Only synthetic schools and manual payments; no gateway calls or live records.
"""
from datetime import date

from django.test import TestCase

from core.models import (
    Family, Guardian as CoreGuardian, HouseholdFamilyLink, School,
    UserAccount, UserRole,
)
from finance.models import (
    FinanceAllocation, FinanceDonation, FinanceObligation, FinancePayment,
    FinanceRefund, ObligationType, PaymentStatus, Processor,
)
from finance.services import (
    _resolve_ledger_account_for_user, initiate_refund, ledger_post_donation,
    ledger_post_obligation, settle_payment_and_allocate,
)
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import (
    Allocation as LedgerAllocation, Charge as LedgerCharge, LedgerAccount,
    Payment as LedgerPayment,
)


class LedgerPayerIdentityTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic ledger school")
        self.payer = UserAccount.objects.create_user(
            username="ledger-payer", email="payer@synthetic.invalid",
            school=self.school, password="test-only",
        )
        self.real = Household.objects.create(
            school_id=self.school.id, name="Verified household",
        )
        self.spoof = Household.objects.create(
            school_id=self.school.id, name="Unverified email household",
        )

    def guardian(self, household, *, account=None, email=None):
        return HouseholdGuardian.objects.create(
            school_id=self.school.id, household=household,
            account=account, email=email or "contact@synthetic.invalid",
            first_name="Synthetic", last_name="Guardian",
        )

    def obligation(self):
        return FinanceObligation.objects.create(
            school=self.school, payer_user=self.payer,
            obligation_type=ObligationType.TUITION,
            due_date=date(2026, 12, 1), amount_cents=10000,
            description="Synthetic tuition",
        )

    def payment(self):
        return FinancePayment.objects.create(
            school=self.school, payer_user=self.payer,
            amount_cents=10000, status=PaymentStatus.PENDING,
            processor=Processor.MANUAL,
        )

    def settle(self, payment, obligation):
        return settle_payment_and_allocate(
            payment=payment,
            allocations_payload=[{
                "obligation_id": obligation.id, "amount_cents": 10000,
            }],
        )

    def state(self, payment):
        payment.refresh_from_db()
        return (
            payment.status, FinanceAllocation.objects.count(),
            FinanceRefund.objects.count(), LedgerAccount.objects.count(),
            LedgerPayment.objects.count(), LedgerCharge.objects.count(),
            LedgerAllocation.objects.count(),
        )

    def core_link(self, household):
        family = Family.objects.create(
            school=self.school, family_name="Verified core family",
        )
        guardian = CoreGuardian.objects.create(
            school=self.school, family=family, first_name="Synthetic",
            last_name="Guardian", email="core@synthetic.invalid",
            relationship="OTHER",
        )
        self.payer.guardian = guardian
        self.payer.save(update_fields=["guardian"])
        HouseholdFamilyLink.objects.create(
            school=self.school, family=family, household_id=household.pk,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
        return family

    def test_email_only_obligation_never_creates_ledger_account(self):
        self.guardian(self.spoof, email=self.payer.email)
        self.assertFalse(ledger_post_obligation(self.obligation()).ok)
        self.assertFalse(LedgerAccount.objects.exists())
        self.assertFalse(LedgerCharge.objects.exists())

    def test_email_only_settlement_rolls_back(self):
        self.guardian(self.spoof, email=self.payer.email)
        payment, obligation = self.payment(), self.obligation()
        before = self.state(payment)
        with self.assertRaisesRegex(ValueError, "Ledger posting failed"):
            self.settle(payment, obligation)
        self.assertEqual(self.state(payment), before)

    def test_verified_account_wins_over_unlinked_matching_email(self):
        self.guardian(self.spoof, email=self.payer.email)
        self.guardian(
            self.real, account=self.payer, email="different@synthetic.invalid",
        )
        payment, obligation = self.payment(), self.obligation()
        self.settle(payment, obligation)
        ledger_payment = LedgerPayment.objects.get(
            reference=f"finance_payment:{payment.pk}",
        )
        self.assertEqual(ledger_payment.account.household_id, self.real.id)
        self.assertFalse(LedgerAccount.objects.filter(household=self.spoof).exists())
        self.assertEqual(
            LedgerAllocation.objects.filter(payment=ledger_payment).count(), 1,
        )

    def test_schoolless_payer_with_core_family_bridge_succeeds(self):
        self.payer.school = None
        self.payer.save(update_fields=["school"])
        self.core_link(self.real)
        payment, obligation = self.payment(), self.obligation()
        self.settle(payment, obligation)
        self.assertEqual(
            LedgerPayment.objects.get(
                reference=f"finance_payment:{payment.pk}",
            ).account.household_id,
            self.real.id,
        )

    def test_parent_role_without_guardian_link_does_not_map(self):
        UserRole.objects.create(
            school=self.school, user=self.payer, role_code="PARENT",
        )
        self.guardian(self.spoof, email=self.payer.email)
        payment, obligation = self.payment(), self.obligation()
        before = self.state(payment)
        with self.assertRaisesRegex(ValueError, "Ledger posting failed"):
            self.settle(payment, obligation)
        self.assertEqual(self.state(payment), before)

    def test_conflicting_links_fail_without_ledger_mutation(self):
        self.guardian(self.real, account=self.payer)
        self.core_link(self.spoof)
        self.assertIsNone(_resolve_ledger_account_for_user(
            school_id=self.school.id, user=self.payer,
        ))
        payment, obligation = self.payment(), self.obligation()
        before = self.state(payment)
        with self.assertRaisesRegex(ValueError, "Ledger posting failed"):
            self.settle(payment, obligation)
        self.assertEqual(self.state(payment), before)

    def test_two_core_links_to_different_households_fail_closed(self):
        family = self.core_link(self.real)
        HouseholdFamilyLink.objects.create(
            school=self.school, family=family, household_id=self.spoof.id,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
        self.assertIsNone(_resolve_ledger_account_for_user(
            school_id=self.school.id, user=self.payer,
        ))
        self.assertFalse(LedgerAccount.objects.exists())

    def test_inactive_payer_and_household_denied(self):
        self.guardian(self.real, account=self.payer)
        self.real.is_active = False
        self.real.save(update_fields=["is_active"])
        self.assertIsNone(_resolve_ledger_account_for_user(
            school_id=self.school.id, user=self.payer,
        ))
        self.real.is_active = True
        self.real.save(update_fields=["is_active"])
        self.payer.is_active = False
        self.payer.save(update_fields=["is_active"])
        self.assertIsNone(_resolve_ledger_account_for_user(
            school_id=self.school.id, user=self.payer,
        ))
        self.assertFalse(LedgerAccount.objects.exists())

    def test_revoked_link_cannot_post_refund_and_rolls_back(self):
        self.guardian(self.real, account=self.payer)
        payment, obligation = self.payment(), self.obligation()
        self.settle(payment, obligation)
        HouseholdGuardian.objects.filter(account=self.payer).update(account=None)
        before = self.state(payment)
        with self.assertRaisesRegex(ValueError, "Ledger refund posting failed"):
            initiate_refund(
                payment=payment, amount_cents=1000, processor=Processor.MANUAL,
            )
        self.assertEqual(self.state(payment), before)

    def test_donation_ledger_mapping_requires_verified_link(self):
        donation = FinanceDonation.objects.create(
            school=self.school, donor_user=self.payer,
            amount_cents=2500, fund_code="SYNTHETIC",
        )
        self.guardian(self.spoof, email=self.payer.email)
        self.assertFalse(ledger_post_donation(donation).ok)
        self.assertFalse(LedgerPayment.objects.exists())
        self.guardian(self.real, account=self.payer)
        self.assertTrue(ledger_post_donation(donation).ok)
        self.assertEqual(
            LedgerPayment.objects.get(
                reference=f"finance_donation:{donation.pk}",
            ).account.household_id,
            self.real.id,
        )
