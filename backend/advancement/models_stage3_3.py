"""
Stage 3.3 Models – Section pricing + email outbox.

EventSectionPrice stores per-section ticket prices for an event.
EmailOutbox is a durable outbox for transactional emails (ticket delivery, receipts).
"""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class EventSectionPrice(models.Model):
    """Price (in cents) for a seating section within an event."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event_id = models.UUIDField(db_index=True)
    section = models.CharField(max_length=100)
    # Price in cents (e.g. 2500 = $25.00)
    price_cents = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "event_id", "section")]
        indexes = [
            models.Index(fields=["school_id", "event_id"], name="sectprice_school_event_idx"),
        ]

    def __str__(self) -> str:
        return f"EventSectionPrice event={self.event_id} section={self.section} price={self.price_cents}"


class EmailOutbox(models.Model):
    """
    Durable transactional email outbox.
    A management command (send_outbox) dequeues and delivers rows.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    KIND_CHOICES = [
        ("ticket_delivery", "Ticket Delivery"),
        ("receipt", "Receipt"),
        ("general", "General"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    kind = models.CharField(max_length=40, choices=KIND_CHOICES, default="general")
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body_text = models.TextField(blank=True, default="")
    body_html = models.TextField(blank=True, default="")

    # List of {filename, content_b64, mime_type} dicts
    attachments_json = models.JSONField(default=list)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="emailoutbox_status_created_idx"),
            models.Index(fields=["school_id"], name="emailoutbox_school_idx"),
        ]

    def __str__(self) -> str:
        return f"EmailOutbox({self.kind}) to={self.to_email} status={self.status}"
