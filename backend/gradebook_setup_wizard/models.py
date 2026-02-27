import uuid

from django.conf import settings
from django.db import models

from core.models import School


class GradebookSetupWizardSession(models.Model):
    """
    5-state wizard session for setting up gradebook category weights for a section.

    State machine:
      draft
        → configured       (POST /configure/  — section_id)
        → categories_defined (POST /categories/ — list of category objects)
        → committed        (POST /commit/     — creates AssignmentCategory records)
        → verified         (GET  /verify/     — returns category_count + total_weight)
    """

    STATUS_DRAFT              = "draft"
    STATUS_CONFIGURED         = "configured"
    STATUS_CATEGORIES_DEFINED = "categories_defined"
    STATUS_COMMITTED          = "committed"
    STATUS_VERIFIED           = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,              "Draft"),
        (STATUS_CONFIGURED,         "Configured"),
        (STATUS_CATEGORIES_DEFINED, "Categories Defined"),
        (STATUS_COMMITTED,          "Committed"),
        (STATUS_VERIFIED,           "Verified"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name="gradebook_setup_wizard_sessions")
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="gradebook_setup_wizard_sessions_created",
    )

    section_id   = models.UUIDField(null=True, blank=True)
    # categories: [{"name": "Homework", "weight_percent": 30, "sort_order": 1}, ...]
    categories   = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "gradebook_setup_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"GradebookSetupWizardSession({self.school_id}, section={self.section_id}, {self.status})"
