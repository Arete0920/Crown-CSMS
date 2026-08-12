from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import School
from journal.models import AccountingPeriod, GLAccount
from journal.services import (
    close_accounting_period,
    post_journal_entry,
    reopen_accounting_period,
)


User = get_user_model()


class AccountingPeriodControlTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Period Control School")
        self.user = User.objects.create_user(
            username="period-admin",
            email="period-admin@example.com",
            password="pass1234",
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
        self.period = AccountingPeriod.objects.create(
            school=self.school,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
        )

    def _post(self, posting_date):
        return post_journal_entry(
            school=self.school,
            created_by=self.user,
            posting_date=posting_date,
            lines=[
                {"account": self.cash, "debit": Decimal("100.00")},
                {"account": self.revenue, "credit": Decimal("100.00")},
            ],
            memo="Period control proof",
        )

    def test_open_period_allows_posting_and_records_posting_date(self):
        entry = self._post(date(2026, 8, 12))
        self.assertEqual(entry.posting_date, date(2026, 8, 12))

    def test_closed_period_fails_closed(self):
        close_accounting_period(period=self.period, user=self.user, note="Month-end close")
        with self.assertRaisesRegex(ValidationError, "is closed"):
            self._post(date(2026, 8, 12))

    def test_reopen_requires_reason(self):
        close_accounting_period(period=self.period, user=self.user)
        with self.assertRaisesRegex(ValidationError, "requires a reason"):
            reopen_accounting_period(period=self.period, user=self.user, reason="")

    def test_reopen_with_reason_restores_posting(self):
        close_accounting_period(period=self.period, user=self.user)
        reopened = reopen_accounting_period(
            period=self.period,
            user=self.user,
            reason="Approved correction",
        )
        self.assertEqual(reopened.status, AccountingPeriod.Status.OPEN)
        self.assertIsNotNone(reopened.reopened_at)
        self.assertEqual(reopened.reopened_by, self.user)
        entry = self._post(date(2026, 8, 12))
        self.assertEqual(entry.posting_date, date(2026, 8, 12))

    def test_accounting_periods_cannot_overlap_for_same_school(self):
        overlapping = AccountingPeriod(
            school=self.school,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 9, 15),
        )
        with self.assertRaisesRegex(ValidationError, "cannot overlap"):
            overlapping.full_clean()

    def test_other_school_period_does_not_block_posting(self):
        other_school = School.objects.create(name="Other Period School")
        other_period = AccountingPeriod.objects.create(
            school=other_school,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
        )
        close_accounting_period(period=other_period, user=self.user)
        entry = self._post(date(2026, 8, 12))
        self.assertEqual(entry.school, self.school)
