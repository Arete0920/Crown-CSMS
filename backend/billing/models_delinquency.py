"""
Stage 2 — Grace Period & Auto-Suspension

Tracks delinquency and suspension state at the Household level, which is the
billing unit in the Crown ledger spine (Household → LedgerAccount → Charges/Payments).
"""
import uuid
from django.db import models
from django.utils import timezone


class HouseholdDelinquency(models.Model):
    """
    Records when a household entered delinquency and whether it has been
    suspended from system access.

    Grace period enforcement: enforced by billing.services_grace.enforce_grace_period()
    Default grace period: 30 days from delinquent_since.
    """

    GRACE_PERIOD_DAYS = 30  # read from settings in service; this is the DB default

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    household = models.OneToOneField(
        "households.Household",
        on_delete=models.CASCADE,
        related_name="delinquency_record",
    )

    delinquent_since = models.DateField(null=True, blank=True, db_index=True)
    suspended = models.BooleanField(default=False, db_index=True)
    suspended_at = models.DateTimeField(null=True, blank=True)

    # Reason for most recent suspension (e.g. "grace_period_expired")
    suspension_reason = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "household_delinquency"
        indexes = [
            models.Index(fields=["school_id", "suspended"]),
            models.Index(fields=["school_id", "delinquent_since"]),
        ]

    def __str__(self) -> str:
        s = " [SUSPENDED]" if self.suspended else ""
        return f"HouseholdDelinquency(household={self.household_id}, since={self.delinquent_since}{s})"

    def mark_suspended(self, reason: str = "grace_period_expired") -> None:
        """Mark this household as suspended. Call save() after."""
        self.suspended = True
        self.suspended_at = timezone.now()
        self.suspension_reason = reason
