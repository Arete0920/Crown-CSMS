from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.models import School
from payments.models import BankStatementEntry, BankStatementImport, ProviderPayoutBatch
from payments.reconciliation_ops import auto_match_payout_batches_for_school


class BankReconciliationTests(TestCase):
    def test_auto_match_payout_by_amount_and_date(self):
        school = School.objects.create(name="Recon School")

        statement_import = BankStatementImport.objects.create(
            school_id=school.id,
            source_name="bank.csv",
            status="processed",
            row_count=1,
        )

        BankStatementEntry.objects.create(
            school_id=school.id,
            statement_import=statement_import,
            posted_date=date(2026, 3, 10),
            description="Deposit",
            amount=Decimal("100.00"),
            currency="USD",
        )

        ProviderPayoutBatch.objects.create(
            school_id=school.id,
            provider="compuwerx",
            payout_id="po_123",
            status="settled",
            gross_amount=Decimal("102.00"),
            fee_amount=Decimal("2.00"),
            net_amount=Decimal("100.00"),
            currency="USD",
            expected_payment_count=1,
            settled_at=timezone.datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.get_current_timezone()),
        )

        matched = auto_match_payout_batches_for_school(school_id=school.id)
        self.assertEqual(matched, 1)
