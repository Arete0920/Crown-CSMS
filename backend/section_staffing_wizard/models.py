import uuid
from django.conf import settings
from django.db import models


class SectionStaffingWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_SECTIONS_LOADED = "sections_loaded"
    STATUS_ASSIGNMENTS_STAGED = "assignments_staged"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_SECTIONS_LOADED, "Sections Loaded"),
        (STATUS_ASSIGNMENTS_STAGED, "Assignments Staged"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="section_staffing_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # UUID reference to academic year (no FK — app decoupled)
    academic_year_id = models.UUIDField(null=True, blank=True)
    term = models.CharField(max_length=24, blank=True, default="")
    # [{section_id, section_name, course_code, grade_level}]
    sections_pool = models.JSONField(default=list)
    # [{section_id, teacher_id, role: "primary"|"aide"|"co-teacher"}]
    assignments = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SectionStaffingWizard {self.id} [{self.term}] ({self.status})"
