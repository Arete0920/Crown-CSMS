"""
analytics/services_health.py

Customer health scoring engine.
Computes a composite 0-100 score per school from observable signals.
"""
from analytics.models_customer_health import CustomerHealth


def calculate_health(school_id) -> int:
    """
    Return overall health score 0-100 for school_id.
    TODO: Replace placeholders with real signal queries when telemetry is wired.

    Signal sources (planned):
      login_frequency_score  — login events per 30d vs active user count
      payment_failure_score  — % failed payments in last 90d (lower = better)
      support_ticket_score   — open critical/high tickets per seat (lower = better)
    """
    # Placeholder scores — replace with real queries when signals are available
    login_score = 90
    payment_score = 85
    support_score = 95

    overall = round((login_score + payment_score + support_score) / 3)
    return overall


def upsert_customer_health(school_id) -> CustomerHealth:
    """Compute and persist the health record for a school."""
    # Placeholder scores
    login_score = 90
    payment_score = 85
    support_score = 95
    overall = round((login_score + payment_score + support_score) / 3)

    record, _ = CustomerHealth.objects.update_or_create(
        school_id=school_id,
        defaults={
            "login_frequency_score": login_score,
            "payment_failure_score": payment_score,
            "support_ticket_score": support_score,
            "overall_score": overall,
        },
    )
    return record
