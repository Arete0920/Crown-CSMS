import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import School
from journal.models import GLAccount, JournalEntry
from journal.services import create_reversal_entry, post_journal_entry


User = get_user_model()


class JournalInvariantTests(TestCase):

    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.user = User.objects.create_user(
            username="tester",
            email="test@example.com",
            password="pass1234"
        )

        self.cash = GLAccount.objects.create(
            school=self.school,
            code="1000",
            name="Cash",
            account_type="ASSET",
        )

        self.revenue = GLAccount.objects.create(
            school=self.school,
            code="4000",
            name="Tuition Revenue",
            account_type="REVENUE",
        )

    def _balanced_lines(self, amount=Decimal("100.00")):
        return [
            {"account": self.cash, "debit": amount},
            {"account": self.revenue, "credit": amount},
        ]

    def test_balanced_entry_succeeds(self):
        entry = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=self._balanced_lines(),
            memo="Tuition payment",
        )

        self.assertTrue(entry.locked)
        self.assertEqual(entry.lines.count(), 2)

    def test_unbalanced_entry_fails(self):
        with self.assertRaises(ValidationError):
            post_journal_entry(
                school=self.school,
                created_by=self.user,
                lines=[
                    {"account": self.cash, "debit": Decimal("100.00")},
                    {"account": self.revenue, "credit": Decimal("90.00")},
                ],
            )

    def test_single_line_fails(self):
        with self.assertRaises(ValidationError):
            post_journal_entry(
                school=self.school,
                created_by=self.user,
                lines=[
                    {"account": self.cash, "debit": Decimal("100.00")},
                ],
            )

    def test_negative_values_fail(self):
        with self.assertRaises(ValidationError):
            post_journal_entry(
                school=self.school,
                created_by=self.user,
                lines=[
                    {"account": self.cash, "debit": Decimal("-1.00")},
                    {"account": self.revenue, "credit": Decimal("1.00")},
                ],
            )

    def test_cross_tenant_account_fails(self):
        other_school = School.objects.create(name="Other School")

        other_account = GLAccount.objects.create(
            school=other_school,
            code="1001",
            name="Other Cash",
            account_type="ASSET",
        )

        with self.assertRaises(ValidationError):
            post_journal_entry(
                school=self.school,
                created_by=self.user,
                lines=[
                    {"account": other_account, "debit": Decimal("100.00")},
                    {"account": self.revenue, "credit": Decimal("100.00")},
                ],
            )

    def test_locked_entry_cannot_be_modified(self):
        entry = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=self._balanced_lines(),
        )

        entry.memo = "Changed"
        with self.assertRaises(ValidationError):
            entry.save()

    def test_locked_entry_cannot_be_deleted(self):
        entry = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=self._balanced_lines(),
        )

        with self.assertRaises(ValidationError):
            entry.delete()

    def test_atomicity_on_failure(self):
        try:
            post_journal_entry(
                school=self.school,
                created_by=self.user,
                lines=[
                    {"account": self.cash, "debit": Decimal("100.00")},
                    {"account": self.revenue, "credit": Decimal("90.00")},
                ],
            )
        except ValidationError:
            pass

        self.assertEqual(JournalEntry.objects.count(), 0)

    def test_accounting_traceability_metadata_is_persisted(self):
        correlation_id = uuid.uuid4()
        entry = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=self._balanced_lines(),
            reference_type="charge",
            reference_id=uuid.uuid4(),
            correlation_id=correlation_id,
            source_system="student_accounts",
            currency="usd",
        )

        self.assertEqual(entry.correlation_id, correlation_id)
        self.assertEqual(entry.source_system, "student_accounts")
        self.assertEqual(entry.currency, "USD")

    def test_empty_currency_fails_closed(self):
        with self.assertRaises(ValidationError):
            post_journal_entry(
                school=self.school,
                created_by=self.user,
                lines=self._balanced_lines(),
                currency="",
            )

    def test_reversal_is_idempotent_and_preserves_traceability(self):
        reference_id = uuid.uuid4()
        correlation_id = uuid.uuid4()
        original = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=self._balanced_lines(),
            reference_type="payment",
            reference_id=reference_id,
            correlation_id=correlation_id,
            source_system="payments",
            currency="USD",
        )

        first = create_reversal_entry(original_entry=original, reason="payment voided")
        second = create_reversal_entry(original_entry=original, reason="retry")

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(JournalEntry.objects.filter(reversal_of=original).count(), 1)
        self.assertEqual(first.reference_type, "payment_reversal")
        self.assertEqual(first.reference_id, reference_id)
        self.assertEqual(first.correlation_id, correlation_id)
        self.assertEqual(first.source_system, "payments")
        self.assertEqual(first.currency, "USD")

        original_lines = list(original.lines.order_by("account_id"))
        reversal_lines = list(first.lines.order_by("account_id"))
        self.assertEqual(len(original_lines), len(reversal_lines))
        for original_line, reversal_line in zip(original_lines, reversal_lines, strict=True):
            self.assertEqual(reversal_line.debit, original_line.credit)
            self.assertEqual(reversal_line.credit, original_line.debit)
