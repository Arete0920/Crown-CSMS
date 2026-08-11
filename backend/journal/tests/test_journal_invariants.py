from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import School
from journal.models import GLAccount, JournalEntry
from journal.services import post_journal_entry


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

    def test_balanced_entry_succeeds(self):
        entry = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=[
                {"account": self.cash, "debit": Decimal("100.00")},
                {"account": self.revenue, "credit": Decimal("100.00")},
            ],
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
            lines=[
                {"account": self.cash, "debit": Decimal("100.00")},
                {"account": self.revenue, "credit": Decimal("100.00")},
            ],
        )

        entry.memo = "Changed"
        with self.assertRaises(ValidationError):
            entry.save()

    def test_locked_entry_cannot_be_deleted(self):
        entry = post_journal_entry(
            school=self.school,
            created_by=self.user,
            lines=[
                {"account": self.cash, "debit": Decimal("100.00")},
                {"account": self.revenue, "credit": Decimal("100.00")},
            ],
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
