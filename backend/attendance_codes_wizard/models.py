import uuid
from django.conf import settings
from django.db import models


class AttendanceCodesWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_CODES_STAGED = "codes_staged"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_CODES_STAGED, "Codes Staged"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="attendance_codes_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # {"school_year": str, "applies_to_grades": [...]}
    policy_config = models.JSONField(default=dict)
    # [{code: str, label: str, excused: bool, counts_as_tardy: bool,
    #   counts_as_absent: bool, notify_guardian: bool}]
    codes_staged = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AttendanceCodesWizard {self.id} ({self.status})"
