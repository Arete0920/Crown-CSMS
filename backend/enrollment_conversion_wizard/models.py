import uuid

from django.conf import settings
from django.db import models

from core.models import School


class EnrollmentConversionWizardSession(models.Model):
    """
    5-state wizard session for converting accepted applicants to enrolled students.

    State machine:
      draft
        → configured       (POST /configure/       — academic_year_label + from_status)
        → applicants_loaded (POST /load/            — queries AdmissionsApplication)
        → committed        (POST /commit/           — bulk updates status → ENROLLED)
        → verified         (GET  /verify/           — returns enrolled_count)
    """

    STATUS_DRAFT             = "draft"
    STATUS_CONFIGURED        = "configured"
    STATUS_APPLICANTS_LOADED = "applicants_loaded"
    STATUS_COMMITTED         = "committed"
    STATUS_VERIFIED          = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,             "Draft"),
        (STATUS_CONFIGURED,        "Configured"),
        (STATUS_APPLICANTS_LOADED, "Applicants Loaded"),
        (STATUS_COMMITTED,         "Committed"),
        (STATUS_VERIFIED,          "Verified"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name="enrollment_conversion_wizard_sessions")
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="enrollment_conversion_wizard_sessions_created",
    )

    academic_year_label = models.CharField(max_length=16, default="")   # e.g., "2026-2027"
    from_status         = models.CharField(max_length=24, default="ACCEPTED")
    application_ids     = models.JSONField(default=list)                 # list of UUID strings
    commit_result       = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "enrollment_conversion_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"EnrollmentConversionWizardSession({self.school_id}, {self.academic_year_label!r}, {self.status})"
