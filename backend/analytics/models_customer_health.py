"""
analytics/models_customer_health.py

CustomerHealth — one-per-school composite health score.
Updated by the health-score engine (services_health.py).
"""
from django.db import models


class CustomerHealth(models.Model):
    """Composite health score for a school tenant."""
    school_id = models.UUIDField(unique=True, db_index=True)

    # Component scores (0-100)
    login_frequency_score = models.IntegerField(default=0)
    payment_failure_score = models.IntegerField(default=0)
    support_ticket_score = models.IntegerField(default=0)

    # Composite (weighted average of components)
    overall_score = models.IntegerField(default=0)

    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["school_id"]

    def __str__(self):
        return f"CustomerHealth(school={self.school_id}, score={self.overall_score})"
