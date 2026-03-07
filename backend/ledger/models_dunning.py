"""
Stage 2 — Financial & Revenue Integrity

Dunning and chargeback models.  These extend the existing ledger spine without
touching the immutable Payment fields.

DunningRecord  : tracks retry state per failed Payment
Chargeback     : dispute/chargeback case against a Payment
DailyPayoutAudit : nightly payout reconciliation snapshot
"""
import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone


class DunningRecord(models.Model):
    """
    Tracks the retry lifecycle for a failed ledger Payment.

    Deliberately separate from Payment to preserve ImmutableMoneyMixin
    invariants on the spine model.

    Retry ladder (days after previous attempt):
        attempt 1 → immediate
        attempt 2 → +2 days
        attempt 3 → +5 days
        attempt 4 → +10 days → delinquent
    """

    RETRY_SCHEDULE_DAYS = [0, 2, 5, 10]  # day offsets per attempt (0 = immediate)

    STATUS_PENDING = "pending"
    STATUS_RETRYING = "retrying"
    STATUS_RESOLVED = "resolved"
    STATUS_DELINQUENT = "delinquent"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RETRYING, "Retrying"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_DELINQUENT, "Delinquent"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    # FK to the existing spine Payment — do not modify Payment itself.
    payment = models.OneToOneField(
        "ledger.Payment",
        on_delete=models.CASCADE,
        related_name="dunning_record",
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Processor reference captured on each retry (append-only via audit log)
    processor_reference = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dunning_record"
        indexes = [
            models.Index(fields=["school_id", "status"]),
            models.Index(fields=["school_id", "next_retry_at"]),
        ]

    def __str__(self) -> str:
        return f"DunningRecord(payment={self.payment_id}, attempt={self.attempt_count}, status={self.status})"

    @property
    def max_attempts_reached(self) -> bool:
        return self.attempt_count >= len(self.RETRY_SCHEDULE_DAYS)


class Chargeback(models.Model):
    """
    Tracks a payment dispute / chargeback case.
    One chargeback per payment (a payment may be re-disputed but we keep history).
    """

    STATUS_OPEN = "open"
    STATUS_WON = "won"
    STATUS_LOST = "lost"
    STATUS_WITHDRAWN = "withdrawn"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_WON, "Won"),
        (STATUS_LOST, "Lost"),
        (STATUS_WITHDRAWN, "Withdrawn"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    payment = models.ForeignKey(
        "ledger.Payment",
        on_delete=models.CASCADE,
        related_name="chargebacks",
    )

    dispute_reason = models.TextField()
    dispute_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    opened_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "chargeback"
        indexes = [
            models.Index(fields=["school_id", "dispute_status"]),
            models.Index(fields=["school_id", "opened_at"]),
        ]

    def __str__(self) -> str:
        return f"Chargeback(payment={self.payment_id}, status={self.dispute_status}, amount={self.amount})"


class DailyPayoutAudit(models.Model):
    """
    Nightly snapshot of expected vs actual processor payout.
    Captured by management command run_daily_payout_audit.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    audit_date = models.DateField(db_index=True)
    expected_total = models.DecimalField(max_digits=12, decimal_places=2)
    actual_total = models.DecimalField(max_digits=12, decimal_places=2)
    variance = models.DecimalField(max_digits=12, decimal_places=2)
    verified = models.BooleanField(default=False)

    # Raw processor response (JSON blob) — stored for audit trail, never exposed via API
    processor_snapshot_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "daily_payout_audit"
        indexes = [
            models.Index(fields=["school_id", "audit_date"]),
            models.Index(fields=["school_id", "verified"]),
        ]
        constraints = [
            # One audit record per school per day
            models.UniqueConstraint(
                fields=["school_id", "audit_date"],
                name="uniq_daily_payout_audit_school_date",
            )
        ]

    def __str__(self) -> str:
        v = "✓" if self.verified else "✗"
        return f"DailyPayoutAudit({self.audit_date}, variance={self.variance} {v})"
