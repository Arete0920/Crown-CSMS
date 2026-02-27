import uuid

from django.conf import settings
from django.db import models

from core.models import School


class AttendanceRulesWizardSession(models.Model):
    """
    5-state wizard session for defining attendance codes and rules.

    State machine:
      draft
        → configured    (POST /configure/    — label + school_year)
        → codes_defined (POST /codes/        — list of code objects)
        → committed     (POST /commit/       — marks rules as official; idempotent)
        → verified      (GET  /verify/       — returns code_count)
    """

    STATUS_DRAFT         = "draft"
    STATUS_CONFIGURED    = "configured"
    STATUS_CODES_DEFINED = "codes_defined"
    STATUS_COMMITTED     = "committed"
    STATUS_VERIFIED      = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,         "Draft"),
        (STATUS_CONFIGURED,    "Configured"),
        (STATUS_CODES_DEFINED, "Codes Defined"),
        (STATUS_COMMITTED,     "Committed"),
        (STATUS_VERIFIED,      "Verified"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name="attendance_rules_wizard_sessions")
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="attendance_rules_wizard_sessions_created",
    )

    label       = models.CharField(max_length=128, default="")
    school_year = models.CharField(max_length=24, default="")
    # codes: [{"code": "P", "label": "Present", "excused": false, "counts_absent": false}, ...]
    codes       = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "attendance_rules_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"AttendanceRulesWizardSession({self.school_id}, {self.label!r}, {self.status})"
