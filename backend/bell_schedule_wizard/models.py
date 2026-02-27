import uuid

from django.conf import settings
from django.db import models

from core.models import School


class BellScheduleWizardSession(models.Model):
    """
    5-state wizard session for defining a school's daily bell schedule.

    State machine:
      draft
        → configured      (POST /configure/ — label + school_year)
        → periods_defined (POST /periods/   — list of period objects)
        → committed       (POST /commit/    — marks schedule as official; idempotent)
        → verified        (GET  /verify/    — returns period_count)
    """

    STATUS_DRAFT          = "draft"
    STATUS_CONFIGURED     = "configured"
    STATUS_PERIODS_DEFINED = "periods_defined"
    STATUS_COMMITTED      = "committed"
    STATUS_VERIFIED       = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,           "Draft"),
        (STATUS_CONFIGURED,      "Configured"),
        (STATUS_PERIODS_DEFINED, "Periods Defined"),
        (STATUS_COMMITTED,       "Committed"),
        (STATUS_VERIFIED,        "Verified"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name="bell_schedule_wizard_sessions")
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="bell_schedule_wizard_sessions_created",
    )

    label       = models.CharField(max_length=128, default="")
    school_year = models.CharField(max_length=24, default="")
    # periods: [{"name": "Period 1", "start_time": "08:00", "end_time": "08:50", "days": ["Mon",...]}]
    periods     = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "bell_schedule_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"BellScheduleWizardSession({self.school_id}, {self.label!r}, {self.status})"
