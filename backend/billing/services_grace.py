"""
Stage 2 — Grace Period & Auto-Suspension Service

Enforces the configurable grace period for delinquent households.
Called by management command enforce_grace_period (or Celery beat).

Default grace: 30 days from delinquent_since.
Override via settings.CROWN_GRACE_PERIOD_DAYS.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from billing.models_delinquency import HouseholdDelinquency

logger = logging.getLogger("crown.audit")

_DEFAULT_GRACE_DAYS = 30


def _grace_days() -> int:
    return int(getattr(settings, "CROWN_GRACE_PERIOD_DAYS", _DEFAULT_GRACE_DAYS))


def enforce_grace_period(*, school_id) -> dict:
    """
    Find HouseholdDelinquency records for exactly one school that have exceeded
    the grace period and mark them suspended.

    Returns: {school_id, suspended_count, grace_days}
    """
    grace_days = _grace_days()
    cutoff = timezone.now().date() - timedelta(days=grace_days)

    to_suspend = HouseholdDelinquency.objects.filter(
        school_id=school_id,
        delinquent_since__lte=cutoff,
        suspended=False,
        delinquent_since__isnull=False,
    ).select_for_update(skip_locked=True)

    suspended_count = 0

    with transaction.atomic():
        for record in to_suspend:
            record.mark_suspended(reason="grace_period_expired")
            record.save(
                update_fields=["suspended", "suspended_at", "suspension_reason", "updated_at"]
            )
            suspended_count += 1
            logger.warning(
                "grace_period: SUSPENDED household=%s school=%s delinquent_since=%s",
                record.household_id,
                record.school_id,
                record.delinquent_since,
            )

    logger.info("grace_period: school=%s suspended=%d", school_id, suspended_count)
    return {
        "school_id": str(school_id),
        "suspended_count": suspended_count,
        "grace_days": grace_days,
    }
