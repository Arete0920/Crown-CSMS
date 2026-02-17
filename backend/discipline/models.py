from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models

class DisciplineIncident(models.Model):
    """
    Demo-ready discipline incident model:
    - school-scoped (tenant)
    - student-scoped
    - timeline supported via DisciplineAction
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # NOTE: assumes core.School and core.Student exist in your project.
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="discipline_incidents")
    student = models.ForeignKey("core.Student", on_delete=models.CASCADE, related_name="discipline_incidents")

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="discipline_reported")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="discipline_assigned")

    occurred_at = models.DateTimeField()
    location = models.CharField(max_length=120, blank=True, default="")

    CATEGORY_CHOICES = [
        ("tardy", "Tardy"),
        ("dress_code", "Dress Code"),
        ("disruption", "Disruption"),
        ("disrespect", "Disrespect"),
        ("bullying", "Bullying"),
        ("academic_dishonesty", "Academic Dishonesty"),
        ("other", "Other"),
    ]
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="other")

    SEVERITY_CHOICES = [
        ("minor", "Minor"),
        ("moderate", "Moderate"),
        ("major", "Major"),
    ]
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="minor")

    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Investigating"),
        ("closed", "Closed"),
    ]
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")

    summary = models.CharField(max_length=180)
    details = models.TextField(blank=True, default="")

    parent_notified = models.BooleanField(default=False)
    parent_notified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status", "severity"]),
            models.Index(fields=["school", "occurred_at"]),
            models.Index(fields=["school", "student"]),
        ]
        ordering = ["-occurred_at"]

    def __str__(self) -> str:
        return f"Incident({self.student_id}, {self.category}, {self.severity}, {self.status})"


class DisciplineAction(models.Model):
    """
    Timeline log for an incident (demo-friendly, audit-ish).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    incident = models.ForeignKey(DisciplineIncident, on_delete=models.CASCADE, related_name="actions")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    ACTION_CHOICES = [
        ("created", "Created"),
        ("note", "Note"),
        ("assigned", "Assigned"),
        ("parent_notified", "Parent Notified"),
        ("status_changed", "Status Changed"),
        ("closed", "Closed"),
    ]
    action_type = models.CharField(max_length=32, choices=ACTION_CHOICES, default="note")
    note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["incident", "created_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Action({self.action_type})"
