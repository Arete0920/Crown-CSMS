import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import School
from journal.models import GLAccount, JournalEntry
from journal.services import create_reversal_entry, post_journal_entry


class OptionAAccountingContractTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Option A Accounting")
        self.user = get_user_model().objects.create_user(username="acct", password="pass")
        self.cash = GLAccount.objects.create(school=self.school, code="1000", name="Cash", account_type="ASSET")
        self.revenue = GLAccount.objects.create(school=self.school, code="4000", name="Revenue", account_type="REVENUE")

    def _post(self, **kwargs):
        return post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=[
                {"account": self.cash, "debit": Decimal("10.00")},
                {"account": self.revenue, "credit": Decimal("10.00")},
            ],
            **kwargs,
        )

    def test_traceability_metadata_persists_and_normalizes_currency(self):
        correlation_id = uuid.uuid4()
        entry = self._post(correlation_id=correlation_id, source_system="student_accounts", currency="usd")
        self.assertEqual((entry.correlation_id, entry.source_system, entry.currency), (correlation_id, "student_accounts", "USD"))

    def test_empty_currency_fails_closed(self):
        with self.assertRaises(ValidationError):
            self._post(currency="")

    def test_reversal_is_idempotent_and_preserves_traceability(self):
        reference_id, correlation_id = uuid.uuid4(), uuid.uuid4()
        original = self._post(
            reference_type="payment",
            reference_id=reference_id,
            correlation_id=correlation_id,
            source_system="payments",
        )
        first = create_reversal_entry(original_entry=original, reason="void")
        second = create_reversal_entry(original_entry=original, reason="retry")
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(JournalEntry.objects.filter(reversal_of=original).count(), 1)
        self.assertEqual(
            (first.reference_type, first.reference_id, first.correlation_id, first.source_system, first.currency),
            ("payment_reversal", reference_id, correlation_id, "payments", "USD"),
        )
        original_line = original.lines.order_by("account_id").first()
        reversed_line = first.lines.order_by("account_id").first()
        self.assertEqual((reversed_line.debit, reversed_line.credit), (original_line.credit, original_line.debit))
