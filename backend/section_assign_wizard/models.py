import uuid
from django.conf import settings
from django.db import models


class SectionAssignWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_STUDENTS_LOADED = "students_loaded"
    STATUS_ROSTER_STAGED = "roster_staged"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_STUDENTS_LOADED, "Students Loaded"),
        (STATUS_ROSTER_STAGED, "Roster Staged"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="section_assign_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # Reference to academics.Section (UUID, no FK to keep app decoupled)
    section_id = models.UUIDField(null=True, blank=True)
    term = models.CharField(max_length=24, blank=True, default="")
    # Pool of student UUIDs to choose from (loaded in step 3)
    student_pool = models.JSONField(default=list)
    # List of {student_id: str, action: "add"|"remove"}
    roster_changes = models.JSONField(default=list)
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
        return f"SectionAssignWizard {self.id} [{self.term}] ({self.status})"
