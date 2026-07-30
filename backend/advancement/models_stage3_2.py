"""
Stage 3.2 Models – provider-neutral seat ordering pipeline.

PendingSeatOrder tracks a buyer's intent to purchase specific seats through a deferred provider-neutral checkout flow.
ProcessedWebhookEvent ensures idempotent webhook processing.
"""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class PendingSeatOrder(models.Model):
    """
    Created when a buyer initiates a provider-neutral checkout for a set of seats.
    Transitions: pending → fulfilled | expired | failed
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("fulfilled", "Fulfilled"),
        ("expired", "Expired"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event_id = models.UUIDField(db_index=True)

    # Buyer identity
    purchaser_name = models.CharField(max_length=255)
    purchaser_email = models.EmailField()

    # Seats reserved for this order (list of UUID strings)
    seat_ids = models.JSONField(default=list)

    # Amount in cents (e.g. 2500 = $25.00)
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=10, default="usd")

    # Provider tracking
    provider = models.CharField(max_length=40, default="fake")
    provider_session_id = models.CharField(max_length=255, blank=True, default="")
    provider_payment_intent_id = models.CharField(max_length=255, blank=True, default="")

    # Checkout redirect URL (provider-hosted page or local success URL for the in-process test double)
    checkout_url = models.URLField(max_length=1024, blank=True, default="")

    # Order lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "event_id"], name="pendingorder_school_event_idx"),
            models.Index(fields=["provider_session_id"], name="pendingorder_session_idx"),
        ]

    def touch(self) -> None:
        """Update updated_at timestamp without triggering other signals."""
        self.updated_at = timezone.now()
        self.save(update_fields=["updated_at"])

    def __str__(self) -> str:
        return f"PendingSeatOrder({self.id}) {self.status} by {self.purchaser_email}"


class ProcessedWebhookEvent(models.Model):
    """
    Idempotency guard for webhook processing.
    Each provider+event_id combination is stored once; duplicate webhooks are ignored.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(null=True, blank=True, db_index=True)
    provider = models.CharField(max_length=40, db_index=True)
    # The provider's event ID
    event_id = models.CharField(max_length=255, unique=True)
    processed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self) -> str:
        return f"ProcessedWebhookEvent({self.provider}:{self.event_id})"
