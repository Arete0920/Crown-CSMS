"""
Stage 2 — Dunning Service (Failed Payment Retry Engine)

Retry ladder:
    Attempt 1: immediate (day 0)
    Attempt 2: +2 days
    Attempt 3: +5 days
    Attempt 4: +10 days → mark delinquent

Called by: python manage.py run_dunning_cycle
Also callable directly: from ledger.services_dunning import process_failed_payments
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ledger.models_dunning import DunningRecord

logger = logging.getLogger("crown.audit")

# Day offsets from date of previous attempt (index = attempt_count after attempt)
RETRY_SCHEDULE = [0, 2, 5, 10]


def process_failed_payments() -> dict:
    """
    Process all DunningRecords that are due for retry.

    Returns a summary dict: {retried, delinquent, skipped}
    """
    now = timezone.now()
    due_records = DunningRecord.objects.filter(
        status__in=[DunningRecord.STATUS_PENDING, DunningRecord.STATUS_RETRYING],
        next_retry_at__lte=now,
    ).select_for_update(skip_locked=True)

    retried = 0
    delinquent = 0
    skipped = 0

    with transaction.atomic():
        for record in due_records:
            if record.max_attempts_reached:
                _mark_delinquent(record)
                delinquent += 1
            else:
                try:
                    _retry_payment(record)
                    retried += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "dunning: retry failed for record=%s: %s", record.id, exc
                    )
                    skipped += 1

    logger.info(
        "dunning_cycle: retried=%d delinquent=%d skipped=%d",
        retried,
        delinquent,
        skipped,
    )
    return {"retried": retried, "delinquent": delinquent, "skipped": skipped}


def _retry_payment(record: DunningRecord) -> None:
    """
    Execute a payment retry attempt.

    The actual processor call is a stub — replace this with your payment
    processor SDK call (Stripe, etc.) before enabling in production.
    """
    record.attempt_count += 1
    record.last_attempt_at = timezone.now()
    record.status = DunningRecord.STATUS_RETRYING

    # Schedule next retry window
    if record.attempt_count < len(RETRY_SCHEDULE):
        delay_days = RETRY_SCHEDULE[record.attempt_count]
        record.next_retry_at = timezone.now() + timedelta(days=delay_days)
    else:
        # No more retries after this — next cycle will delinquent it
        record.next_retry_at = timezone.now()

    # ──────────────────────────────────────────────────────────────
    # TODO: replace stub with real processor call, e.g.:
    #   result = stripe.PaymentIntent.confirm(record.processor_reference)
    #   if result.status == "succeeded":
    #       record.status = DunningRecord.STATUS_RESOLVED
    # ──────────────────────────────────────────────────────────────

    record.save(update_fields=[
        "attempt_count", "last_attempt_at", "status", "next_retry_at", "updated_at"
    ])

    logger.info(
        "dunning: retried payment=%s attempt=%d next_retry=%s",
        record.payment_id,
        record.attempt_count,
        record.next_retry_at,
    )


def _mark_delinquent(record: DunningRecord) -> None:
    """Escalate to delinquent after exhausting all retry attempts."""
    record.status = DunningRecord.STATUS_DELINQUENT
    record.save(update_fields=["status", "updated_at"])

    logger.warning(
        "dunning: DELINQUENT payment=%s after %d attempts",
        record.payment_id,
        record.attempt_count,
    )


def register_failed_payment(*, payment, school_id) -> DunningRecord:
    """
    Called when a payment fails for the first time.
    Creates a DunningRecord and schedules the first immediate retry.
    """
    record, created = DunningRecord.objects.get_or_create(
        payment=payment,
        defaults={
            "school_id": school_id,
            "status": DunningRecord.STATUS_PENDING,
            "attempt_count": 0,
            "next_retry_at": timezone.now(),  # immediate first retry
        },
    )
    if created:
        logger.info("dunning: registered failed payment=%s", payment.id)
    return record
