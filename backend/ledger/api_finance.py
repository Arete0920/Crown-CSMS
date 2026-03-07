"""
Stage 2 — CFO Finance API

Read-only endpoints for the Finance & Revenue Integrity dashboard.

Endpoints:
    GET /api/v1/finance/kpis/              — reconciliation + revenue summary
    GET /api/v1/finance/chargebacks/       — open dispute metrics
    GET /api/v1/finance/monthly-summary/   — CFO monthly rollup
    GET /api/v1/finance/payout-audit/      — recent daily payout audits

All endpoints require authentication.
School scoping: uses X-School-Id header (same pattern as rest of spine).
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from households.scoping import get_request_school_id
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def finance_kpis(request):
    """
    GET /api/v1/finance/kpis/

    Returns reconciliation summary and revenue totals.
    Processor transactions are stubbed — wire real processor API here.
    """
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    # TODO: replace empty list with real processor API call
    processor_transactions: list[dict] = []

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
    """
    GET /api/v1/finance/chargebacks/

    Returns open chargeback count and total disputed amount.
    """
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
    """
    GET /api/v1/finance/monthly-summary/

    CFO-grade monthly rollup: revenue, chargebacks, net.
    """
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    summary = build_monthly_summary(school_id=school_id)

    return JsonResponse({"ok": True, **summary})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payout_audit_list(request):
    """
    GET /api/v1/finance/payout-audit/

    Returns the 30 most recent daily payout audit records for this school.
    """
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    audits = (
        DailyPayoutAudit.objects.filter(school_id=school_id)
        .order_by("-audit_date")[:30]
    )

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
    """
    GET /api/v1/finance/dunning/

    Returns count of records by dunning status for the school.
    """
    school_id, err = _school_id_or_400(request)
    if err:
        return err

    counts = {}
    for status_value, _ in DunningRecord.STATUS_CHOICES:
        counts[status_value] = DunningRecord.objects.filter(
            school_id=school_id, status=status_value
        ).count()

    return JsonResponse({"ok": True, "dunning": counts})
