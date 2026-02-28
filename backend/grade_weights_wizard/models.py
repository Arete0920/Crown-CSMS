import uuid
from django.conf import settings
from django.db import models


class GradeWeightsWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_CATEGORIES_STAGED = "categories_staged"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_CATEGORIES_STAGED, "Categories Staged"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="grade_weights_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # UUID of the gradebook/course section being configured (null until step 2)
    gradebook_id = models.UUIDField(null=True, blank=True)
    marking_period = models.CharField(max_length=24, blank=True)
    # [{name: str, weight_pct: int, drop_lowest: int, description: str}]
    # sum(weight_pct) must equal 100 at commit time
    categories_staged = models.JSONField(default=list)
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
        return f"GradeWeightsWizard {self.id} ({self.status})"
