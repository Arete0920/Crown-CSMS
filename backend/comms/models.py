"""
CROWN Communications models.

OutboxMessage is defined here (canonical) so Django's ORM, migrations,
and admin all resolve it through the standard app label `comms`.
outbox.py re-exports from here for backward-compat imports.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Outbox — reliable async message delivery
# ---------------------------------------------------------------------------

class OutboxMessage(models.Model):
    """
    Persistent outbox entry. Written atomically with the business operation,
    drained by the Celery worker (comms/tasks.py) with exponential backoff.
    """

    STATUS_PENDING = "PENDING"
    STATUS_SENT    = "SENT"
    STATUS_FAILED  = "FAILED"
    STATUS_DEAD    = "DEAD"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT,    "Sent"),
        (STATUS_FAILED,  "Failed (retrying)"),
        (STATUS_DEAD,    "Dead (max retries)"),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id       = models.CharField(max_length=64, db_index=True)
    channel         = models.CharField(max_length=32)          # EMAIL | SMS | PUSH | TEAMS
    to              = models.TextField()
    subject         = models.TextField(blank=True, default="")
    body            = models.TextField()
    idempotency_key = models.CharField(max_length=128, unique=True)
    status          = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    attempts        = models.IntegerField(default=0)
    last_error      = models.TextField(blank=True, default="")
    next_attempt_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    sent_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "comms"
        indexes = [
            models.Index(fields=["status", "next_attempt_at"]),
            models.Index(fields=["school_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"OutboxMessage({self.channel} → {self.to} [{self.status}])"


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------

class NotificationPreference(models.Model):
    """Per-user channel opt-in settings."""

    user          = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference")
    email_enabled = models.BooleanField(default=True)
    sms_enabled   = models.BooleanField(default=False)
    teams_enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"NotificationPreference({self.user})"


# ---------------------------------------------------------------------------
# Message log (delivery receipts)
# ---------------------------------------------------------------------------

class MessageLog(models.Model):
    """Delivery record for every message sent through CROWN."""

    CHANNEL_CHOICES = (
        ("email", "Email"),
        ("sms",   "SMS"),
        ("teams", "Teams"),
        ("inapp", "In-App"),
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_messages",
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_messages",
    )

    channel          = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    subject          = models.CharField(max_length=255, blank=True)
    body             = models.TextField()

    external_id      = models.CharField(max_length=255, blank=True, null=True)
    delivery_status  = models.CharField(max_length=50, default="pending")
    error_message    = models.TextField(blank=True, null=True)

    created_at       = models.DateTimeField(auto_now_add=True)
    delivered_at     = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"MessageLog({self.channel}, {self.delivery_status}, "
            f"{self.created_at:%Y-%m-%d})"
        )
