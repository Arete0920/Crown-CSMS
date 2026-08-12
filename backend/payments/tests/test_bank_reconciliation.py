from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from core.models import School, UserAccount
from payments.models import (
    BankStatementEntry,
    BankStatementImport,
    PayoutBankMatch,
    PayoutBankMatchStatus,
    ProviderPayoutBatch,
)
from payments.reconciliation_ops import (
    AUTO_MATCH_RULE,
    auto_match_payout_batches_for_school,
    create_manual_payout_match,
)


class BankReconciliationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Recon School")
        self.statement_import = BankStatementImport.objects.create(
            school_id=self.school.id,
            source_name="bank.csv",
            status="processed",
            row_count=1,
        )
        self.user = UserAccount.objects.create_user(
            username="recon-user",
            email="recon@example.test",
            password="test-only-password",
            school=self.school,
        )

    def bank_entry(
        self,
        *,
        amount="100.00",
        currency="USD",
        posted_date=date(2026, 3, 10),
        reference="bank-1",
    ):
        return BankStatementEntry.objects.create(
            school_id=self.school.id,
            statement_import=self.statement_import,
            posted_date=posted_date,
            description="Deposit",
            reference=reference,
            amount=Decimal(amount),
            currency=currency,
        )

    def payout(
        self,
        *,
        payout_id="po_123",
        net_amount="100.00",
        currency="USD",
        settled_at=None,
    ):
        if settled_at is None:
            settled_at = timezone.datetime(
                2026,
                3,
                9,
                12,
                0,
                0,
                tzinfo=timezone.get_current_timezone(),
            )
        return ProviderPayoutBatch.objects.create(
            school_id=self.school.id,
            provider="compuwerx",
            payout_id=payout_id,
            status="settled",
            gross_amount=Decimal("102.00"),
            fee_amount=Decimal("2.00"),
            net_amount=Decimal(net_amount),
            currency=currency,
            expected_payment_count=1,
            settled_at=settled_at,
        )

    def test_auto_match_payout_by_amount_currency_and_settled_date(self):
        bank_entry = self.bank_entry()
        payout = self.payout()

        matched = auto_match_payout_batches_for_school(school_id=self.school.id)

        self.assertEqual(matched, 1)
        bank_entry.refresh_from_db()
        self.assertTrue(bank_entry.is_matched)
        match = payout.bank_matches.get()
        self.assertIn(f"rule={AUTO_MATCH_RULE}", match.note)
        self.assertIn("payout_id=po_123", match.note)
        self.assertIn("bank_reference=bank-1", match.note)

    def test_auto_match_skips_currency_mismatch(self):
        self.bank_entry(currency="CAD")
        self.payout(currency="USD")

        matched = auto_match_payout_batches_for_school(school_id=self.school.id)

        self.assertEqual(matched, 0)

    def test_auto_match_skips_missing_provider_settlement_date(self):
        self.bank_entry()
        payout = self.payout()
        payout.settled_at = None
        payout.save(update_fields=["settled_at"])

        matched = auto_match_payout_batches_for_school(school_id=self.school.id)

        self.assertEqual(matched, 0)

    def test_auto_match_fails_closed_on_ambiguous_best_bank_candidates(self):
        self.bank_entry(reference="bank-a")
        self.bank_entry(reference="bank-b")
        self.payout()

        matched = auto_match_payout_batches_for_school(school_id=self.school.id)

        self.assertEqual(matched, 0)

    def test_auto_match_fails_closed_when_bank_entry_has_competing_payouts(self):
        self.bank_entry()
        self.payout(payout_id="po_a")
        self.payout(payout_id="po_b")

        matched = auto_match_payout_batches_for_school(school_id=self.school.id)

        self.assertEqual(matched, 0)

    def test_manual_match_is_idempotent_for_same_pair_and_blocks_reuse(self):
        bank_entry = self.bank_entry(reference="manual-bank-1")
        payout = self.payout(payout_id="manual-po-1")

        first = create_manual_payout_match(
            school_id=self.school.id,
            payout_batch=payout,
            bank_entry=bank_entry,
            user=self.user,
            note="Reviewed against bank statement.",
        )
        replay = create_manual_payout_match(
            school_id=self.school.id,
            payout_batch=payout,
            bank_entry=bank_entry,
            user=self.user,
            note="Replay must not create a second fact.",
        )

        self.assertEqual(replay.pk, first.pk)

        another_payout = self.payout(payout_id="manual-po-2")
        with self.assertRaisesRegex(ValueError, "Bank statement entry is already actively matched"):
            create_manual_payout_match(
                school_id=self.school.id,
                payout_batch=another_payout,
                bank_entry=bank_entry,
                user=self.user,
            )

        another_bank = self.bank_entry(reference="manual-bank-2")
        with self.assertRaisesRegex(ValueError, "Payout batch is already actively matched"):
            create_manual_payout_match(
                school_id=self.school.id,
                payout_batch=payout,
                bank_entry=another_bank,
                user=self.user,
            )

    def test_manual_match_requires_actor_settlement_date_and_same_currency(self):
        bank_entry = self.bank_entry(currency="CAD")
        payout = self.payout(currency="USD")

        with self.assertRaisesRegex(ValueError, "authenticated finance user"):
            create_manual_payout_match(
                school_id=self.school.id,
                payout_batch=payout,
                bank_entry=bank_entry,
                user=None,
            )

        with self.assertRaisesRegex(ValueError, "currency must match"):
            create_manual_payout_match(
                school_id=self.school.id,
                payout_batch=payout,
                bank_entry=bank_entry,
                user=self.user,
            )

        same_currency_bank = self.bank_entry(currency="USD", reference="missing-date-bank")
        payout.settled_at = None
        payout.save(update_fields=["settled_at"])
        with self.assertRaisesRegex(ValueError, "settlement date evidence"):
            create_manual_payout_match(
                school_id=self.school.id,
                payout_batch=payout,
                bank_entry=same_currency_bank,
                user=self.user,
            )

    def test_database_constraints_block_active_payout_and_bank_reuse(self):
        first_bank = self.bank_entry(reference="db-bank-1")
        second_bank = self.bank_entry(reference="db-bank-2")
        first_payout = self.payout(payout_id="db-po-1")
        second_payout = self.payout(payout_id="db-po-2")

        first = PayoutBankMatch.objects.create(
            school_id=self.school.id,
            payout_batch=first_payout,
            bank_entry=first_bank,
            status=PayoutBankMatchStatus.AUTO_MATCHED,
        )
        self.assertIsNotNone(first.pk)

        with self.assertRaises(IntegrityError), transaction.atomic():
            PayoutBankMatch.objects.create(
                school_id=self.school.id,
                payout_batch=first_payout,
                bank_entry=second_bank,
                status=PayoutBankMatchStatus.MANUAL_MATCHED,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            PayoutBankMatch.objects.create(
                school_id=self.school.id,
                payout_batch=second_payout,
                bank_entry=first_bank,
                status=PayoutBankMatchStatus.MANUAL_MATCHED,
            )

    def test_reconciliation_relationships_protect_evidence_from_cascade_delete(self):
        bank_entry = self.bank_entry(reference="protected-bank")
        payout = self.payout(payout_id="protected-payout")
        create_manual_payout_match(
            school_id=self.school.id,
            payout_batch=payout,
            bank_entry=bank_entry,
            user=self.user,
        )

        with self.assertRaises(ProtectedError):
            payout.delete()
        with self.assertRaises(ProtectedError):
            bank_entry.delete()