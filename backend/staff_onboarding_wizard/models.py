"""
staff_onboarding_wizard/models.py

Tracks a single staff-member creation wizard session.

State machine:
  draft
    → configured   (POST /configure/  — first_name, last_name, email, role_type)
    → previewed    (GET  /preview/    — show what will be created)
    → committed    (POST /commit/     — creates core.Staff record)
    → verified     (GET  /verify/     — confirms the Staff record exists)
"""
import uuid

from django.conf import settings
from django.db import models

from core.models import School


class StaffOnboardingWizardSession(models.Model):
    STATUS_DRAFT      = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_PREVIEWED  = "previewed"
    STATUS_COMMITTED  = "committed"
    STATUS_VERIFIED   = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,      "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_PREVIEWED,  "Previewed"),
        (STATUS_COMMITTED,  "Committed"),
        (STATUS_VERIFIED,   "Verified"),
    ]

    ROLE_TEACHER  = "TEACHER"
    ROLE_DIRECTOR = "DIRECTOR"
    ROLE_ADMIN    = "ADMIN"
    ROLE_SUPPORT  = "SUPPORT"

    ROLE_CHOICES = [
        (ROLE_TEACHER,  "Teacher"),
        (ROLE_DIRECTOR, "Director"),
        (ROLE_ADMIN,    "Admin"),
        (ROLE_SUPPORT,  "Support"),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school     = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="staff_onboarding_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_onboarding_wizard_sessions_created",
    )

    # Collected during configure step
    first_name = models.CharField(max_length=100, blank=True)
    last_name  = models.CharField(max_length=100, blank=True)
    email      = models.EmailField(blank=True)
    role_type  = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)

    # Populated after commit
    commit_result = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "staff_onboarding_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return (
            f"StaffOnboardingWizardSession("
            f"{self.school_id}, {self.email!r}, {self.status})"
        )
