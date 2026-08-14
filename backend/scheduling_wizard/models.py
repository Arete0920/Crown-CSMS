import uuid
from django.conf import settings
from django.db import models


class SchedulingWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_COURSES_SAVED = "courses_saved"
    STATUS_SECTIONS_STAGED = "sections_staged"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_COURSES_SAVED, "Courses Saved"),
        (STATUS_SECTIONS_STAGED, "Sections Staged"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="scheduling_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="scheduling_wizard_sessions",
    )
    term_ref = models.ForeignKey(
        "academics.Term",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="scheduling_wizard_sessions",
    )
    # Legacy display/compatibility fields retained during cutover.
    term = models.CharField(max_length=24, blank=True, default="")
    school_year = models.CharField(max_length=16, blank=True, default="")
    courses_config = models.JSONField(default=list)
    sections_config = models.JSONField(default=list)
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
        term_label = self.term_ref.code if self.term_ref_id else self.term
        return f"SchedulingWizard {self.id} [{term_label}] ({self.status})"
