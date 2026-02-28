from __future__ import annotations
import uuid
from django.conf import settings
from django.db import models
from core.models import School


class StaffMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="wizard_staff_members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="staff_memberships",
    )
    email = models.EmailField()
    first_name = models.CharField(max_length=80, blank=True, default="")
    last_name = models.CharField(max_length=80, blank=True, default="")
    is_teacher = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "email"], name="uniq_staff_email_per_school"),
        ]


class StaffSetupWizardSession(models.Model):
    STATUS = [
        ("draft", "Draft"),
        ("configured", "Configured"),
        ("committed", "Committed"),
        ("verified", "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS, default="draft")
    roster = models.JSONField(default=list, blank=True)
    commit_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
