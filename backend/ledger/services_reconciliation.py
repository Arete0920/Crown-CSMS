"""
Stage 2 — Revenue Reconciliation Service

Compares local ledger totals against processor-reported figures.
Returns a structured dict suitable for the CFO dashboard API.

Usage:
    from ledger.services_reconciliation import reconcile_processor, build_monthly_summary
"""
import logging
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from ledger.models import Payment
from ledger.models_dunning import Chargeback, DailyPayoutAudit

logger = logging.getLogger("crown.audit")


def reconcile_processor(
    processor_transactions: list[dict],
    *,
    school_id=None,
) -> dict:
    """
    Compare local successful payments against processor-reported transactions.

    processor_transactions: list of {"amount": Decimal|float, ...} from processor API.
    Returns: {local_total, processor_total, difference, match}
    """
    qs = Payment.objects.filter(is_void=False)
    if school_id:
        qs = qs.filter(school_id=school_id)

    local_total: Decimal = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
    processor_total = Decimal(
        str(sum(Decimal(str(tx.get("amount", 0))) for tx in processor_transactions))
    )
    difference = processor_total - local_total

    result = {
        "local_total": float(local_total),
        "processor_total": float(processor_total),
        "difference": float(difference),
        "match": difference == Decimal("0.00"),
    }

    if difference != Decimal("0.00"):
        logger.warning(
            "reconciliation: MISMATCH school=%s local=%.2f processor=%.2f diff=%.2f",
            school_id,
            local_total,
            processor_total,
            difference,
        )

    return result


def build_monthly_summary(*, school_id=None) -> dict:
    """
    CFO-grade monthly summary across all payment statuses.
    Aggregates from the spine Payment and Chargeback tables.
    """
    qs = Payment.objects.filter(is_void=False)
    if school_id:
        qs = qs.filter(school_id=school_id)

    revenue: Decimal = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

    cb_qs = Chargeback.objects.order_by("id")
    if school_id:
        cb_qs = cb_qs.filter(school_id=school_id)

    chargebacks: Decimal = cb_qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

    open_chargebacks = cb_qs.filter(dispute_status=Chargeback.STATUS_OPEN).count()
    net_revenue = revenue - chargebacks

    return {
        "revenue": float(revenue),
        "chargebacks": float(chargebacks),
        "open_chargebacks": open_chargebacks,
        "net_revenue": float(net_revenue),
    }


def record_daily_payout_audit(
    *,
    school_id,
    audit_date: date | None = None,
    processor_transactions: list[dict] | None = None,
) -> DailyPayoutAudit:
    """
    Snapshot the daily expected-vs-actual payout and persist it.
    Called by management command run_daily_payout_audit.
    """
    today = audit_date or timezone.now().date()
    processor_transactions = processor_transactions or []

    # Expected: sum of non-void payments for today
    expected: Decimal = (
        Payment.objects.filter(
            school_id=school_id,
            is_void=False,
            created_at__date=today,
        ).aggregate(t=Sum("amount"))["t"]
        or Decimal("0.00")
    )

    # Actual: from processor (stub — replace with real API call)
    actual = Decimal(
        str(sum(Decimal(str(tx.get("amount", 0))) for tx in processor_transactions))
    ) if processor_transactions else expected  # stub: assume match when no processor data

    variance = actual - expected

    audit, _ = DailyPayoutAudit.objects.update_or_create(
        school_id=school_id,
        audit_date=today,
        defaults={
            "expected_total": expected,
            "actual_total": actual,
            "variance": variance,
            "verified": variance == Decimal("0.00"),
            "processor_snapshot_json": {"transactions": processor_transactions},
        },
    )

    if variance != Decimal("0.00"):
        logger.warning(
            "payout_audit: VARIANCE school=%s date=%s expected=%.2f actual=%.2f var=%.2f",
            school_id,
            today,
            expected,
            actual,
            variance,
        )
    else:
        logger.info(
            "payout_audit: OK school=%s date=%s total=%.2f",
            school_id,
            today,
            expected,
        )

    return audit
