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


@require_http_methods(["GET"])
def teacher_metrics(request):
    """Teacher dashboard — today's schedule, attendance, assignments."""
    return JsonResponse({
        "sections_today":           5,
        "attendance_taken":         3,
        "attendance_pending":       2,
        "assignments_to_grade":    14,
        "missing_submissions_count": 7,
        "students_at_risk_count":   3,
        "alerts": [
            {"label": "2 sections still need attendance logged",      "severity": "yellow"},
            {"label": "3 students below 70% — may need intervention", "severity": "red"},
            {"label": "14 ungraded submissions pending",              "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def parent_metrics(request):
    """Parent dashboard — child grades, missing work, messages, balance."""
    return JsonResponse({
        "children": [
            {
                "name": "Jordan",
                "grade": "9th",
                "gpa": 3.4,
                "missing_assignments": 1,
                "attendance_flags": 0,
                "upcoming_events": 2,
            },
            {
                "name": "Morgan",
                "grade": "6th",
                "gpa": 3.8,
                "missing_assignments": 0,
                "attendance_flags": 1,
                "upcoming_events": 1,
            },
        ],
        "balance_due":       1_250,
        "messages_unread":   2,
        "alerts": [
            {"label": "Jordan has 1 missing assignment in English",    "severity": "yellow"},
            {"label": "Morgan has 1 attendance flag — Feb 19",         "severity": "yellow"},
            {"label": "Balance due: $1,250 — due Mar 1",               "severity": "red"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def student_metrics(request):
    """Student dashboard — today's schedule, assignments due, grade snapshot."""
    return JsonResponse({
        "periods_today":         7,
        "assignments_due_today": 3,
        "assignments_missing":   1,
        "current_gpa":           3.6,
        "grade_snapshot": [
            {"subject": "English",  "grade": "A-", "pct": 91},
            {"subject": "Math",     "grade": "B+", "pct": 88},
            {"subject": "History",  "grade": "A",  "pct": 95},
            {"subject": "Science",  "grade": "B",  "pct": 84},
            {"subject": "Spanish",  "grade": "A-", "pct": 92},
        ],
        "alerts": [
            {"label": "1 overdue assignment — Math (due Feb 20)", "severity": "red"},
            {"label": "History quiz tomorrow — 3rd period",        "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def it_metrics(request):
    """IT Director dashboard — system health, open tickets, device compliance."""
    return JsonResponse({
        "api_status":             "ok",
        "db_status":              "ok",
        "last_deploy_tag":        "prod-deploy-2026-02-22-1415",
        "last_deploy_sha":        "d196ab66",
        "open_tickets":           5,
        "overdue_tickets":        1,
        "total_devices":          148,
        "devices_compliant":      141,
        "devices_non_compliant":  7,
        "cert_expiry_days":       42,
        "failed_checks":          0,
        "alerts": [
            {"label": "SSL cert expires in 42 days",         "severity": "yellow"},
            {"label": "7 devices out of compliance",         "severity": "yellow"},
            {"label": "Open ticket older than 14 days (x1)", "severity": "red"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def financial_aid_metrics(request):
    """Financial Aid Director dashboard — applications, budget, overdue decisions."""
    return JsonResponse({
        "applications_submitted": 47,
        "applications_in_review": 18,
        "applications_decided":   29,
        "decisions_overdue":       6,
        "budget_total":          380_000,
        "budget_awarded":        312_500,
        "budget_remaining":       67_500,
        "avg_award":               3_906,
        "needs_buckets": [
            {"label": "Full (100%)",    "count": 4},
            {"label": "High (75–99%)",  "count": 8},
            {"label": "Mid (50–74%)",   "count": 11},
            {"label": "Low (<50%)",     "count": 6},
        ],
        "alerts": [
            {"label": "6 applications with decisions overdue >7 days", "severity": "red"},
            {"label": "Budget 82% allocated with 18 reviews pending",  "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def marketing_metrics(request):
    """Marketing & Advancement dashboard — inquiry funnel, source mix, campaigns."""
    return JsonResponse({
        "inquiries_ytd":   187,
        "tours_scheduled":  62,
        "applications":     54,
        "enrolled":         38,
        "stalled_leads":    11,
        "inquiry_sources": [
            {"source": "Website",  "count": 74, "pct": 40},
            {"source": "Referral", "count": 56, "pct": 30},
            {"source": "Social",   "count": 37, "pct": 20},
            {"source": "Event",    "count": 20, "pct": 10},
        ],
        "campaigns": [
            {"name": "Spring Open House", "status": "active",   "leads": 28, "conversions": 9},
            {"name": "Digital Ads Q1",    "status": "active",   "leads": 41, "conversions": 12},
            {"name": "Referral Drive",    "status": "complete", "leads": 18, "conversions": 7},
        ],
        "alerts": [
            {"label": "11 leads with no follow-up >7 days",    "severity": "red"},
            {"label": "Open House RSVPs below target (28/50)", "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def spiritual_life_metrics(request):
    """Spiritual Life Director dashboard — chapel, service hours, pastoral care."""
    return JsonResponse({
        "chapel_sessions_this_month":  8,
        "avg_chapel_attendance_pct":  91,
        "service_hours_ytd":        1_240,
        "service_hours_goal":       2_000,
        "care_referrals_open":          4,
        "care_referrals_resolved_mtd": 11,
        "support_flagged_students":     3,
        "upcoming_chapel": [
            {"date": "Feb 24", "topic": "Faith in Community",   "speaker": "Chaplain Davis"},
            {"date": "Feb 26", "topic": "Service & Calling",    "speaker": "Guest — Rev. Park"},
            {"date": "Mar 3",  "topic": "Chapel Worship Night", "speaker": "Student Led"},
        ],
        "alerts": [
            {"label": "3 students flagged for pastoral follow-up", "severity": "yellow"},
            {"label": "4 open care referrals pending assignment",  "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
def office_metrics(request):
    """Office Manager / HR dashboard — staff absences, requests, HR tasks, compliance."""
    return JsonResponse({
        "staff_absent_today":   3,
        "coverage_gaps":        1,
        "open_requests":        7,
        "hr_tasks_due":         4,
        "compliance_items_due": 2,
        "recent_requests": [
            {"label": "Facility repair — gym HVAC",          "status": "open",      "priority": "high"},
            {"label": "Supply order — classroom consumables", "status": "pending",   "priority": "normal"},
            {"label": "Background check — new hire",         "status": "in_review", "priority": "high"},
            {"label": "Leave request — T. Williams",         "status": "approved",  "priority": "normal"},
            {"label": "Vendor invoice — janitorial svc",     "status": "pending",   "priority": "normal"},
        ],
        "hr_tasks": [
            {"label": "Annual TB test due — 2 staff",      "due": "Feb 28"},
            {"label": "I-9 reverification — 1 staff",      "due": "Mar 5"},
            {"label": "Handbook acknowledgment — 4 staff", "due": "Mar 10"},
            {"label": "Emergency contact update",           "due": "Mar 15"},
        ],
        "alerts": [
            {"label": "1 coverage gap today — Period 3 sub needed", "severity": "red"},
            {"label": "2 compliance items due this week",            "severity": "yellow"},
            {"label": "3 staff absent — substitutes placed",         "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })
