import uuid

from django.conf import settings
from django.db import models

from core.models import School


class CommsWizardSession(models.Model):
    """
    6-state wizard session for configuring and queuing a communication campaign.

    State machine:
      draft
        → configured      (POST /configure/ — purpose + channels)
        → message_drafted (POST /message/ — subject + body)
        → recipients_staged (POST /recipients/ — list of {to: "email"})
        → committed       (POST /commit/ — writes OutboxMessage records)
        → verified        (GET  /verify/)
    """

    STATUS_DRAFT              = "draft"
    STATUS_CONFIGURED         = "configured"
    STATUS_MESSAGE_DRAFTED    = "message_drafted"
    STATUS_RECIPIENTS_STAGED  = "recipients_staged"
    STATUS_COMMITTED          = "committed"
    STATUS_VERIFIED           = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,             "Draft"),
        (STATUS_CONFIGURED,        "Configured"),
        (STATUS_MESSAGE_DRAFTED,   "Message Drafted"),
        (STATUS_RECIPIENTS_STAGED, "Recipients Staged"),
        (STATUS_COMMITTED,         "Committed"),
        (STATUS_VERIFIED,          "Verified"),
    ]

    VALID_CHANNELS = {"email", "sms", "teams"}

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name="comms_wizard_sessions")
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="comms_wizard_sessions_created",
    )

    purpose      = models.CharField(max_length=128, default="")
    channels     = models.JSONField(default=list)   # ["email", "sms", "teams"]
    subject      = models.CharField(max_length=255, default="")
    body         = models.TextField(default="")
    recipients   = models.JSONField(default=list)   # [{"to": "addr@example.com", "name": "..."}]
    commit_result = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "comms_wizard"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "status"]),
        ]

    def __str__(self) -> str:
        return f"CommsWizardSession({self.school_id}, {self.status})"
