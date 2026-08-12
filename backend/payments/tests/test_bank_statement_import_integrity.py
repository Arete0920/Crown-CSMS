from django.test import TestCase

from core.models import School
from payments.bank_recon_api import _process_bank_statement_bytes
from payments.models import BankStatementEntry, BankStatementImport, BankStatementImportStatus


class BankStatementImportIntegrityTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Statement Integrity School")
        self.import_row = BankStatementImport.objects.create(
            school_id=self.school.id,
            source_name="statement.csv",
            status=BankStatementImportStatus.UPLOADED,
        )

    def test_invalid_later_row_rolls_back_entire_statement(self):
        raw = (
            b"posted_date,description,reference,amount,currency\n"
            b"2026-03-10,Valid deposit,bank-1,100.00,usd\n"
            b"not-a-date,Invalid deposit,bank-2,50.00,USD\n"
        )

        with self.assertRaisesRegex(ValueError, "Invalid or missing posted_date"):
            _process_bank_statement_bytes(import_row=self.import_row, raw_bytes=raw)

        self.assertEqual(BankStatementEntry.objects.filter(statement_import=self.import_row).count(), 0)
        self.import_row.refresh_from_db()
        self.assertEqual(self.import_row.status, BankStatementImportStatus.UPLOADED)
        self.assertEqual(self.import_row.row_count, 0)

    def test_successful_statement_normalizes_currency_and_records_row_count(self):
        raw = (
            b"posted_date,description,reference,amount,currency\n"
            b"2026-03-10,Deposit,bank-1,100.00,usd\n"
        )

        rows = _process_bank_statement_bytes(import_row=self.import_row, raw_bytes=raw)

        self.assertEqual(rows, 1)
        entry = BankStatementEntry.objects.get(statement_import=self.import_row)
        self.assertEqual(entry.currency, "USD")
        self.import_row.refresh_from_db()
        self.assertEqual(self.import_row.status, BankStatementImportStatus.PROCESSED)
        self.assertEqual(self.import_row.row_count, 1)
        self.assertIsNotNone(self.import_row.processed_at)

    def test_statement_with_no_data_rows_fails_closed(self):
        raw = b"posted_date,description,reference,amount,currency\n"

        with self.assertRaisesRegex(ValueError, "no valid data rows"):
            _process_bank_statement_bytes(import_row=self.import_row, raw_bytes=raw)

        self.assertFalse(BankStatementEntry.objects.filter(statement_import=self.import_row).exists())