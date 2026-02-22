"""
Crown2026 – Dashboard Metrics Views
Read-only JSON endpoints for the three persona dashboards.

Endpoints registered in crown_api/api_urls.py:
  GET /api/v1/admin/metrics/
  GET /api/v1/board/metrics/
  GET /api/v1/finance/metrics/

These return stable JSON shapes that the frontend dashboards consume.
Demo-realistic numbers are hardcoded for MVP; real model queries can replace
each value later without changing the response shape.
"""

import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def _today() -> str:
    return datetime.date.today().isoformat()


@require_http_methods(["GET"])
def admin_metrics(request):
    """
    Administration dashboard – principal / operations.

    Returns today-at-a-glance, enrollment funnel, operational alerts.
    """
    return JsonResponse({
        # Top KPI tiles
        "enrolled": 312,
        "attendance_flags_today": 7,
        "discipline_incidents_week": 3,
        "messages_pending": 14,
        "billing_delinquencies": 11,

        # Enrollment funnel (current academic year)
        "enrollment_funnel": {
            "inquiries": 87,
            "applicants": 54,
            "admitted": 41,
            "enrolled": 38,
        },

        # Operational alerts list
        "operational_alerts": [
            {"type": "overdue_form",   "label": "Overdue enrollment forms",       "count": 4},
            {"type": "missing_doc",    "label": "Missing health records",          "count": 9},
            {"type": "staff_coverage", "label": "Staff coverage gaps this week",   "count": 2},
            {"type": "comms",          "label": "Unanswered family messages >48h", "count": 6},
        ],

        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def board_metrics(request):
    """
    School Board dashboard – governance / mission / finance oversight.
    """
    return JsonResponse({
        # Enrollment vs target
        "enrollment": {
            "current":        312,
            "target":         340,
            "waitlist":       23,
            "retention_pct":  91.2,
        },

        # Finance health (proxy figures — AR + collections)
        "finance_health": {
            "tuition_billed":    2_180_000,
            "tuition_collected": 1_943_000,
            "collection_pct":    89.1,
            "aid_awarded":       312_500,
            "ar_90_plus":        48_200,
        },

        # Mission & culture indicators
        "mission": {
            "survey_pulse_avg":        4.3,    # out of 5
            "service_hours_ytd":       1842,
            "chapel_attendance_pct":   94,
        },

        # Compliance & risk
        "compliance": {
            "safety_incidents_ytd":    2,
            "audit_log_entries_30d":   5841,
            "required_checks_passing": 7,
        },

        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def finance_metrics(request):
    """
    Finance dashboard – business office view.

    AR aging, collections, financial aid, and operational counters.
    """
    return JsonResponse({
        # Top KPI tiles
        "ar_outstanding":       237_000,
        "collected_this_month": 184_500,
        "aid_awarded":          312_500,
        "payment_failures":     3,

        # AR aging buckets
        "ar_aging": [
            {"bucket": "0\u201330 days",  "amount": 98_400, "count": 42},
            {"bucket": "31\u201360 days", "amount": 71_200, "count": 28},
            {"bucket": "61\u201390 days", "amount": 19_200, "count": 9},
            {"bucket": "90+ days",        "amount": 48_200, "count": 17},
        ],

        # Collections breakdown
        "collections": {
            "paid_this_week":   23_400,
            "paid_this_month":  184_500,
            "outstanding":      237_000,
            "payment_methods": {
                "ach":   112_000,
                "card":   54_500,
                "check":  18_000,
            },
        },

        # Financial aid
        "financial_aid": {
            "awarded":           312_500,
            "budget":            380_000,
            "pending_decisions": 8,
            "avg_award":         3_906,
        },

        # Operational counters
        "operational": {
            "payment_failures": 3,
            "refunds":          1,
            "chargebacks":      0,
        },

        "snapshot_date": _today(),
    })
