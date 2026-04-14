"""Customer health scoring engine."""
from __future__ import annotations

from django.db.models import Count, Q
from django.utils import timezone

from analytics.models_customer_health import CustomerHealth
from core.models import UserAccount
from finance.models import FinancePayment, PaymentStatus
from support.models import SupportTicket


def _clamp(score: int | float | None) -> int:
    """Clamp score to 0..100 and tolerate unexpected/null inputs."""
    try:
        normalized = int(round(float(score)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, normalized))


def _login_frequency_score(school_id) -> int:
    horizon = timezone.now() - timezone.timedelta(days=30)
    active_users = UserAccount.objects.filter(school_id=school_id).count()
    if active_users == 0:
        return 0
    logged_in_users = UserAccount.objects.filter(
        school_id=school_id,
        last_login__gte=horizon,
    ).count()
    return _clamp(round((logged_in_users / active_users) * 100))


def _payment_failure_score(school_id) -> int:
    horizon = timezone.now() - timezone.timedelta(days=90)
    totals = FinancePayment.objects.filter(school_id=school_id, created_at__gte=horizon).aggregate(
        total=Count("id"),
        failed=Count("id", filter=Q(status=PaymentStatus.FAILED)),
    )
    total = totals["total"] or 0
    failed = totals["failed"] or 0
    if total == 0:
        return 100
    failure_rate = failed / total
    return _clamp(round((1 - failure_rate) * 100))


def _support_ticket_score(school_id) -> int:
    open_high = SupportTicket.objects.filter(
        school_id=school_id,
        status__in=[SupportTicket.STATUS_OPEN, SupportTicket.STATUS_ESCALATED],
        priority__in=["high", "critical"],
    ).count()
    return _clamp(100 - (open_high * 10))


def calculate_health(school_id) -> int:
    """Return overall health score 0-100 for school_id."""
    login_score = _login_frequency_score(school_id)
    payment_score = _payment_failure_score(school_id)
    support_score = _support_ticket_score(school_id)
    return _clamp(round((login_score + payment_score + support_score) / 3))


def upsert_customer_health(school_id) -> CustomerHealth:
    """Compute and persist the health record for a school."""
    login_score = _login_frequency_score(school_id)
    payment_score = _payment_failure_score(school_id)
    support_score = _support_ticket_score(school_id)
    overall = _clamp(round((login_score + payment_score + support_score) / 3))

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
