"""
support/models.py — SLA-aware support ticket model.
"""
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
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def sla_deadline(self):
        """Return the datetime by which this ticket should be resolved."""
        from datetime import timedelta
        hours = SLA_HOURS.get(self.priority, 48)
        return self.created_at + timedelta(hours=hours)

    def __str__(self):
        return f"SupportTicket({self.id}, {self.priority}, {self.status})"
