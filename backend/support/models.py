"""
support/models.py — SLA-aware support ticket model.
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.db import models


SLA_HOURS = {
    "low": 48,
    "medium": 24,
    "high": 8,
    "critical": 2,
}


class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_ESCALATED = "escalated"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_ESCALATED, "Escalated"),
        (STATUS_CLOSED, "Closed"),
    ]

    school_id = models.UUIDField(db_index=True)
    # Legacy tickets retain unknown ownership until separately verified.
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolution_summary = models.TextField(blank=True, default="", db_default="")

    class Meta:
        ordering = ["-created_at", "-pk"]

    def sla_deadline(self) -> datetime:
        """Return the internal escalation deadline, not a public service promise."""
        hours = SLA_HOURS.get(self.priority, 48)
        return self.created_at + timedelta(hours=hours)

    def __str__(self):
        return f"SupportTicket({self.id}, {self.priority}, {self.status})"


class SupportTicketEvent(models.Model):
    """Actor-attributed create/resolve history with no public mutation endpoint."""

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.PROTECT,
        related_name="events",
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(
        max_length=20,
        choices=[("created", "Created"), ("resolved", "Resolved")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
