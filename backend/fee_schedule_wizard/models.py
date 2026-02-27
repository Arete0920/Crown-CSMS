"""
fee_schedule_wizard/models.py

Three models:

  FeeScheduleWizardSession — tracks a single wizard lifecycle.
  FeeSchedule              — the canonical fee schedule record (committed result).
  FeeLine                  — individual fee line on a schedule.

Session state machine:
  draft
    → configured   (POST /configure/  — name, term, effective_date)
    → lines_set    (POST /lines/      — list of fee line dicts)
    → committed    (POST /commit/     — creates FeeSchedule + FeeLine records)
    → verified     (GET  /verify/     — confirms record counts)
"""
import uuid

from decimal import Decimal
from django.conf import settings
from django.db import models

from core.models import School


# ---------------------------------------------------------------------------
# Wizard session
# ---------------------------------------------------------------------------

class FeeScheduleWizardSession(models.Model):
    STATUS_DRAFT      = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_LINES_SET  = "lines_set"
    STATUS_COMMITTED  = "committed"
    STATUS_VERIFIED   = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,      "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_LINES_SET,  "Lines Set"),
        (STATUS_COMMITTED,  "Committed"),
        (STATUS_VERIFIED,   "Verified"),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school     = models.ForeignKey(
        School, on_delete=models.CASCADE,
        related_name="fee_schedule_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="fee_schedule_wizard_sessions_created",
    )

    # Collected during configure
    schedule_name  = models.CharField(max_length=120, blank=True)
    term           = models.CharField(max_length=24, blank=True)
    effective_date = models.DateField(null=True, blank=True)

    # Collected during lines step — list of dicts:
    # {code, label, amount_cents, kind, frequency, is_required, sort_order}
    lines_config  = models.JSONField(default=list)

    # Set on commit
    commit_result = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "fee_schedule_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"FeeScheduleWizardSession({self.school_id}, {self.schedule_name!r}, {self.status})"


# ---------------------------------------------------------------------------
# Output models (committed by the wizard)
# ---------------------------------------------------------------------------

class FeeSchedule(models.Model):
    """A named fee schedule for a school term."""

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school         = models.ForeignKey(School, on_delete=models.CASCADE, related_name="fee_schedules")
    name           = models.CharField(max_length=120)
    term           = models.CharField(max_length=24, db_index=True)
    effective_date = models.DateField()
    is_active      = models.BooleanField(default=True, db_index=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "fee_schedule_wizard"
        unique_together = ("school", "name")
        ordering = ["-effective_date"]
        indexes = [models.Index(fields=["school", "term"])]

    def __str__(self) -> str:
        return f"FeeSchedule({self.school_id}, {self.name!r}, {self.term})"


class FeeLine(models.Model):
    """Individual fee on a FeeSchedule."""

    KIND_TUITION = "tuition"
    KIND_FEE     = "fee"
    KIND_CHOICES = [
        (KIND_TUITION, "Tuition"),
        (KIND_FEE,     "Fee"),
    ]

    FREQ_ANNUAL    = "annual"
    FREQ_SEMESTER  = "semester"
    FREQ_MONTHLY   = "monthly"
    FREQ_ONE_TIME  = "one_time"
    FREQ_CHOICES = [
        (FREQ_ANNUAL,   "Annual"),
        (FREQ_SEMESTER, "Semester"),
        (FREQ_MONTHLY,  "Monthly"),
        (FREQ_ONE_TIME, "One-time"),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fee_schedule  = models.ForeignKey(FeeSchedule, on_delete=models.CASCADE, related_name="lines")
    code          = models.CharField(max_length=32)
    label         = models.CharField(max_length=120)
    amount_cents  = models.PositiveIntegerField(default=0)
    kind          = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_FEE)
    frequency     = models.CharField(max_length=16, choices=FREQ_CHOICES, default=FREQ_ANNUAL)
    is_required   = models.BooleanField(default=True)
    sort_order    = models.PositiveSmallIntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "fee_schedule_wizard"
        unique_together = ("fee_schedule", "code")
        ordering = ["sort_order", "code"]

    def __str__(self) -> str:
        return f"FeeLine({self.fee_schedule_id}, {self.code}, {self.amount_cents}¢)"
