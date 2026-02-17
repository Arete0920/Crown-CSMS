from __future__ import annotations
import uuid
from django.db import models


class WebhookEvent(models.Model):
    provider = models.CharField(max_length=64)
    event_id = models.CharField(max_length=128)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "event_id"], name="uniq_webhook_provider_event"),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.event_id}"


class TeamsPreviewAudit(models.Model):
    """
    Audit log for demo-mode Teams integration preview.
    No outbound calls are made; this just logs what WOULD be sent.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="teams_preview_audits")
    event_type = models.CharField(max_length=64)   # e.g. discipline_incident, comms_message
    payload = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school","event_type","created_at"])]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"TeamsPreview({self.event_type}, {self.created_at})"
