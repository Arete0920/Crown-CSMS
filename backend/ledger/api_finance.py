"""
Stage 2 - CFO Finance API

Read-only endpoints for the Finance and Revenue Integrity dashboard.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from households.scoping import get_request_school_id
from ledger.models import Payment
from ledger.models_dunning import Chargeback, DailyPayoutAudit, DunningRecord
from ledger.services_reconciliation import build_monthly_summary, reconcile_processor

logger = logging.getLogger("crown.audit")


def _school_id_or_400(request):
    """Extract school_id from request or return a 400 JsonResponse."""
    try:
        return get_request_school_id(request), None
    except Exception:  # noqa: BLE001
        return None, JsonResponse(
            {"ok": False, "error": "X-School-Id header required"}, status=400
        )


def _processor_transactions_for_school(school_id):
    """Build deterministic reconciliation transactions from ledger payments."""
    return [
        {"amount": p.amount, "reference": p.reference, "source": p.source}
        for p in Payment.objects.filter(school_id=school_id, is_void=False).only(
            "amount", "reference", "source"
        )
    ]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def finance_kpis(request):
    """Return reconciliation summary and revenue totals for the school."""
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    processor_transactions = _processor_transactions_for_school(school_id)
    recon = reconcile_processor(processor_transactions, school_id=school_id)
    summary = build_monthly_summary(school_id=school_id)

    return JsonResponse(
        {
            "ok": True,
            "reconciliation": recon,
            "total_successful_payments": summary["revenue"],
            "net_revenue": summary["net_revenue"],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chargeback_metrics(request):
    """Return open chargeback count and disputed totals."""
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    qs = Chargeback.objects.filter(school_id=school_id)
    open_cases = qs.filter(dispute_status=Chargeback.STATUS_OPEN).count()
    total_amount = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
    open_amount = (
        qs.filter(dispute_status=Chargeback.STATUS_OPEN).aggregate(t=Sum("amount"))["t"]
        or Decimal("0.00")
    )

    return JsonResponse(
        {
            "ok": True,
            "open_cases": open_cases,
            "open_disputed_amount": float(open_amount),
            "total_disputed_amount": float(total_amount),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_financial_summary(request):
    """Return monthly rollup: revenue, chargebacks, net."""
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    summary = build_monthly_summary(school_id=school_id)
    return JsonResponse({"ok": True, **summary})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payout_audit_list(request):
    """Return up to 30 most recent daily payout audit records."""
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    audits = DailyPayoutAudit.objects.filter(school_id=school_id).order_by("-audit_date")[:30]

    return JsonResponse(
        {
            "ok": True,
            "audits": [
                {
                    "date": str(a.audit_date),
                    "expected": float(a.expected_total),
                    "actual": float(a.actual_total),
                    "variance": float(a.variance),
                    "verified": a.verified,
                }
                for a in audits
            ],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dunning_status(request):
    """Return count of dunning records by status."""
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    counts = {}
    for status_value, _ in DunningRecord.STATUS_CHOICES:
        counts[status_value] = DunningRecord.objects.filter(
            school_id=school_id, status=status_value
        ).count()

    return JsonResponse({"ok": True, "dunning": counts})
