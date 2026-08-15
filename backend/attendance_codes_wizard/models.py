import uuid

from django.conf import settings
from django.db import models


class AttendanceConfiguration(models.Model):
    """Canonical tenant-scoped attendance policy/configuration authority."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="attendance_configurations",
    )
    school_year = models.CharField(max_length=24)
    label = models.CharField(max_length=128, default="Attendance Policy")
    policy_config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attendance_configurations_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["school_id", "school_year"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "school_year"],
                name="uniq_attendance_config_school_year",
            )
        ]

    def __str__(self):
        return f"AttendanceConfiguration({self.school_id}, {self.school_year})"


class AttendanceCode(models.Model):
    """Canonical attendance code owned by one AttendanceConfiguration."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    configuration = models.ForeignKey(
        AttendanceConfiguration,
        on_delete=models.CASCADE,
        related_name="codes",
    )
    code = models.CharField(max_length=8)
    label = models.CharField(max_length=128)
    excused = models.BooleanField(default=False)
    counts_as_tardy = models.BooleanField(default=False)
    counts_as_absent = models.BooleanField(default=False)
    notify_guardian = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["configuration_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["configuration", "code"],
                name="uniq_attendance_code_per_configuration",
            )
        ]

    def __str__(self):
        return f"AttendanceCode({self.configuration_id}, {self.code})"


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
