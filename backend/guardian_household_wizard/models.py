import uuid
from django.conf import settings
from django.db import models


class GuardianHouseholdWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_HOUSEHOLD_CONFIGURED = "household_configured"
    STATUS_GUARDIANS_ADDED = "guardians_added"
    STATUS_STUDENTS_LINKED = "students_linked"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_HOUSEHOLD_CONFIGURED, "Household Configured"),
        (STATUS_GUARDIANS_ADDED, "Guardians Added"),
        (STATUS_STUDENTS_LINKED, "Students Linked"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="guardian_household_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # {"name": str, "address": {"street": ..., "city": ..., "state": ..., "zip": ...}}
    household_data = models.JSONField(default=dict)
    # [{"name": str, "email": str, "phone": str, "custody_type": "primary"|"secondary"|"none",
    #   "contact_priority": int, "receives_communications": bool}]
    guardian_data = models.JSONField(default=list)
    # [{"student_id": UUID, "relationship": "parent"|"guardian"|"other"}]
    link_data = models.JSONField(default=list)
    commit_result = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"GuardianHouseholdWizard {self.id} ({self.status})"
