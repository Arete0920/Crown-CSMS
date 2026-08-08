"""
Stage 2 — Revenue Integrity Tests

Tests for dunning service, reconciliation service, grace period enforcement,
chargeback model, and CFO API endpoints.
"""
import uuid
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import School
from ledger.models import LedgerAccount, Payment
from ledger.models_dunning import DunningRecord, Chargeback, DailyPayoutAudit
from ledger.services_dunning import process_failed_payments, register_failed_payment
from ledger.services_reconciliation import (
    reconcile_processor,
    build_monthly_summary,
    record_daily_payout_audit,
)
from billing.models_delinquency import HouseholdDelinquency
from billing.services_grace import enforce_grace_period
from households.models import Household


def _school_id() -> uuid.UUID:
    return uuid.UUID("19801b59-8c05-4c84-9312-5d792e4e839d")


def _ensure_school(school_id: uuid.UUID) -> "School":
    school, _ = School.objects.get_or_create(
        id=school_id,
        defaults={"name": f"Test School {school_id}"},
    )
    return school


def _make_household(school_id: uuid.UUID) -> Household:
    _ensure_school(school_id)
    return Household.objects.create(school_id=school_id, name="Test Family")


def _make_ledger_account(household: Household) -> LedgerAccount:
    return LedgerAccount.objects.create(
        school_id=household.school_id,
        household=household,
    )


def _make_payment(account: LedgerAccount, amount="100.00") -> Payment:
    return Payment.objects.create(
        school_id=account.school_id,
        account=account,
        amount=Decimal(amount),
        source="EXTERNAL",
        reference=str(uuid.uuid4()),
    )


class DunningRecordTests(TestCase):
    """Unit tests for DunningRecord model behaviour."""

    def setUp(self):
        self.school_id = _school_id()
        self.hh = _make_household(self.school_id)
        self.account = _make_ledger_account(self.hh)
        self.payment = _make_payment(self.account)

    def test_register_failed_payment_creates_dunning_record(self):
        record = register_failed_payment(payment=self.payment, school_id=self.school_id)
        self.assertEqual(record.payment, self.payment)
        self.assertEqual(record.status, DunningRecord.STATUS_PENDING)
        self.assertEqual(record.attempt_count, 0)

    def test_register_failed_payment_is_idempotent(self):
        r1 = register_failed_payment(payment=self.payment, school_id=self.school_id)
        r2 = register_failed_payment(payment=self.payment, school_id=self.school_id)
        self.assertEqual(r1.id, r2.id)

    def test_max_attempts_reached_when_at_limit(self):
        record = DunningRecord(attempt_count=len(DunningRecord.RETRY_SCHEDULE_DAYS))
        self.assertTrue(record.max_attempts_reached)

    def test_max_attempts_not_reached_below_limit(self):
        record = DunningRecord(attempt_count=0)
        self.assertFalse(record.max_attempts_reached)


class DunningCycleTests(TestCase):
    """Integration tests for the dunning retry engine service."""

    def setUp(self):
        self.school_id = _school_id()
        self.hh = _make_household(self.school_id)
        self.account = _make_ledger_account(self.hh)

    def test_process_failed_payments_retries_due_record(self):
        payment = _make_payment(self.account)
        record = DunningRecord.objects.create(
            school_id=self.school_id,
            payment=payment,
            status=DunningRecord.STATUS_PENDING,
            attempt_count=0,
            next_retry_at=timezone.now() - timedelta(minutes=1),
        )
        result = process_failed_payments()
        self.assertGreaterEqual(result["retried"], 1)

        record.refresh_from_db()
        self.assertEqual(record.attempt_count, 1)
        self.assertEqual(record.status, DunningRecord.STATUS_RETRYING)

    def test_process_failed_payments_marks_delinquent_when_exhausted(self):
        payment = _make_payment(self.account)
        record = DunningRecord.objects.create(
            school_id=self.school_id,
            payment=payment,
            status=DunningRecord.STATUS_RETRYING,
            attempt_count=len(DunningRecord.RETRY_SCHEDULE_DAYS),
            next_retry_at=timezone.now() - timedelta(minutes=1),
        )
        result = process_failed_payments()
        self.assertGreaterEqual(result["delinquent"], 1)

        record.refresh_from_db()
        self.assertEqual(record.status, DunningRecord.STATUS_DELINQUENT)

    def test_process_skips_records_not_yet_due(self):
        payment = _make_payment(self.account)
        DunningRecord.objects.create(
            school_id=self.school_id,
            payment=payment,
            status=DunningRecord.STATUS_PENDING,
            attempt_count=0,
            next_retry_at=timezone.now() + timedelta(days=5),
        )
        result = process_failed_payments()
        self.assertEqual(result["retried"], 0)
        self.assertEqual(result["delinquent"], 0)


class ReconciliationTests(TestCase):
    """Tests for revenue reconciliation service."""

    def setUp(self):
        self.school_id = _school_id()
        self.hh = _make_household(self.school_id)
        self.account = _make_ledger_account(self.hh)

    def test_reconcile_match(self):
        _make_payment(self.account, "250.00")
        result = reconcile_processor(
            [{"amount": "250.00"}], school_id=self.school_id
        )
        self.assertTrue(result["match"])
        self.assertAlmostEqual(result["difference"], 0.0)

    def test_reconcile_mismatch(self):
        _make_payment(self.account, "250.00")
        result = reconcile_processor(
            [{"amount": "300.00"}], school_id=self.school_id
        )
        self.assertFalse(result["match"])
        self.assertAlmostEqual(result["difference"], 50.0)

    def test_monthly_summary_revenue(self):
        _make_payment(self.account, "500.00")
        summary = build_monthly_summary(school_id=self.school_id)
        self.assertGreaterEqual(summary["revenue"], 500.0)
        self.assertIn("net_revenue", summary)
        self.assertIn("chargebacks", summary)


class ChargebackModelTests(TestCase):
    """Tests for Chargeback model."""

    def setUp(self):
        self.school_id = _school_id()
        self.hh = _make_household(self.school_id)
        self.account = _make_ledger_account(self.hh)
        self.payment = _make_payment(self.account, "150.00")

    def test_create_chargeback(self):
        cb = Chargeback.objects.create(
            school_id=self.school_id,
            payment=self.payment,
            dispute_reason="Unauthorized charge",
            amount=Decimal("150.00"),
        )
        self.assertEqual(cb.dispute_status, Chargeback.STATUS_OPEN)
        self.assertIsNone(cb.resolved_at)

    def test_chargeback_status_transitions(self):
        cb = Chargeback.objects.create(
            school_id=self.school_id,
            payment=self.payment,
            dispute_reason="Test",
            amount=Decimal("150.00"),
        )
        cb.dispute_status = Chargeback.STATUS_WON
        cb.resolved_at = timezone.now()
        cb.save()
        cb.refresh_from_db()
        self.assertEqual(cb.dispute_status, Chargeback.STATUS_WON)


class GracePeriodTests(TestCase):
    """Tests for tenant-explicit auto-suspension grace period enforcement."""

    def setUp(self):
        self.school_id = _school_id()
        self.hh = _make_household(self.school_id)

    def test_suspend_after_grace_period(self):
        past_date = timezone.now().date() - timedelta(days=31)
        record = HouseholdDelinquency.objects.create(
            school_id=self.school_id,
            household=self.hh,
            delinquent_since=past_date,
            suspended=False,
        )
        result = enforce_grace_period(school_id=self.school_id)
        self.assertGreaterEqual(result["suspended_count"], 1)

        record.refresh_from_db()
        self.assertTrue(record.suspended)
        self.assertEqual(record.suspension_reason, "grace_period_expired")

    def test_no_suspension_within_grace_period(self):
        recent_date = timezone.now().date() - timedelta(days=5)
        record = HouseholdDelinquency.objects.create(
            school_id=self.school_id,
            household=self.hh,
            delinquent_since=recent_date,
            suspended=False,
        )
        result = enforce_grace_period(school_id=self.school_id)
        self.assertEqual(result["suspended_count"], 0)

        record.refresh_from_db()
        self.assertFalse(record.suspended)

    def test_already_suspended_not_double_counted(self):
        past_date = timezone.now().date() - timedelta(days=60)
        HouseholdDelinquency.objects.create(
            school_id=self.school_id,
            household=self.hh,
            delinquent_since=past_date,
            suspended=True,
        )
        result = enforce_grace_period(school_id=self.school_id)
        self.assertEqual(result["suspended_count"], 0)
