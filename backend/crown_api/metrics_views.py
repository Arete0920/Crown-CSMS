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
from decimal import Decimal

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from billing.models import Invoice
from billing.reconciliation import compute_invoice_balance_due
from core.permissions import require_permission
from households.scoping import get_request_school_id
from ledger.models import Payment


def _today() -> str:
    return datetime.date.today().isoformat()


@require_http_methods(["GET"])
@require_permission("admin.view")
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
@require_permission("board.view")
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
@require_permission("finance.view")
def finance_metrics(request):
    school_id = get_request_school_id(request, required=True)

    invoices = Invoice.objects.filter(school_id=school_id).order_by("-id")

    total_outstanding = Decimal("0.00")
    open_invoices = 0
    total_invoiced = Decimal("0.00")

    for inv in invoices:
        total_amount = Decimal(str(getattr(inv, "total_amount", Decimal("0.00"))))
        total_invoiced += total_amount
        balance_due = compute_invoice_balance_due(inv)
        total_outstanding += balance_due
        if balance_due > 0:
            open_invoices += 1

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    collected_month = (
        Payment.objects.filter(school_id=school_id, created_at__gte=month_start)
        .aggregate(total=Sum("amount"))
        .get("total")
        or Decimal("0.00")
    )

    payment_failures = Payment.objects.filter(school_id=school_id, source="FAILED").count()

    return JsonResponse(
        {
            "open_invoices": open_invoices,
            "ar_outstanding": str(total_outstanding),
            "total_invoiced": str(total_invoiced),
            "collected_month": str(collected_month),
            "payment_failures": payment_failures,
            "snapshot_date": _today(),
        }
    )


@require_http_methods(["GET"])
@require_permission("teacher.view")
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
@require_permission("parent.view")
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
@require_permission("student.view")
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
@require_permission("it.view")
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
@require_permission("financial_aid.view")
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
@require_permission("marketing.view")
def marketing_metrics(request):
    """Tenant-scoped marketing command metrics derived from admissions truth."""
    from applications.models import Application, Applicant, ApplicationEvent

    school_id = get_request_school_id(request, required=True)
    apps = Application.objects.filter(school_id=school_id)
    app_ids = list(apps.values_list("id", flat=True))
    events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)

    inquiry_ids = set(
        events.filter(event_type="inquiry_created").values_list("application_id", flat=True)
    )
    tour_ids = set(
        events.filter(event_type="tour_scheduled").values_list("application_id", flat=True)
    )
    enrolled_ids = set(
        events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True)
    )
    declined_ids = set()
    for row in events.filter(event_type="decision_made").values("application_id", "payload"):
        payload = row.get("payload") or {}
        decision = str(payload.get("decision") or payload.get("status") or "").strip().lower()
        if decision in {"declined", "denied", "rejected"}:
            declined_ids.add(row["application_id"])

    application_ids = set(
        apps.exclude(status="DRAFT").values_list("id", flat=True)
    )
    now = timezone.now()
    stale_cutoff = now - datetime.timedelta(days=7)
    stalled_leads = (
        apps.filter(updated_at__lte=stale_cutoff)
        .exclude(id__in=enrolled_ids)
        .exclude(id__in=declined_ids)
        .count()
    )

    applicants = Applicant.objects.filter(
        school_id=school_id,
        application_id__in=app_ids,
    ).only("application_id", "source")
    source_map = {}
    for applicant in applicants:
        source = str(applicant.source or "Unspecified").strip() or "Unspecified"
        bucket = source_map.setdefault(source, {"applications": set(), "enrolled": set()})
        bucket["applications"].add(applicant.application_id)
        if applicant.application_id in enrolled_ids:
            bucket["enrolled"].add(applicant.application_id)

    inquiry_sources = []
    for source, bucket in source_map.items():
        applications = len(bucket["applications"])
        enrolled = len(bucket["enrolled"])
        inquiry_sources.append(
            {
                "source": source,
                "applications": applications,
                "enrolled": enrolled,
                "conversion_pct": round((enrolled / applications) * 100, 1) if applications else 0.0,
            }
        )
    inquiry_sources.sort(key=lambda row: (-row["applications"], row["source"].lower()))

    total_applications = len(application_ids)
    total_enrolled = len(enrolled_ids)
    overall_conversion_pct = round((total_enrolled / total_applications) * 100, 1) if total_applications else 0.0

    from crm_marketing.models import MarketingCampaign
    from crm_marketing.services import build_campaign_snapshot

    campaign_snapshots = [
        build_campaign_snapshot(campaign)
        for campaign in MarketingCampaign.objects.filter(school_id=school_id).select_related("academic_year")[:8]
    ]

    action_queue = []
    if stalled_leads:
        action_queue.append(
            {
                "title": f"Re-engage {stalled_leads} stalled prospect record(s)",
                "detail": "No admissions movement recorded in more than seven days.",
                "state": "Action Required",
                "priority": "high",
            }
        )
    if inquiry_ids:
        action_queue.append(
            {
                "title": f"Advance {len(inquiry_ids)} active inquiry record(s)",
                "detail": "Move qualified families toward tours and applications.",
                "state": "Ready",
                "priority": "normal",
            }
        )
    for snapshot in campaign_snapshots:
        empty_seats = snapshot.get("capacity", {}).get("empty_seats")
        if snapshot.get("status") == "active" and isinstance(empty_seats, int) and empty_seats > 0:
            action_queue.append(
                {
                    "title": f"{snapshot['name']}: {empty_seats} target-grade seat(s) remain open",
                    "detail": "Review campaign funnel, follow-ups, affordability path, and channel performance.",
                    "state": "Ready",
                    "priority": "normal",
                }
            )

    return JsonResponse(
        {
            "inquiries": len(inquiry_ids),
            "tours_scheduled": len(tour_ids),
            "applications": total_applications,
            "enrolled": total_enrolled,
            "stalled_leads": stalled_leads,
            "overall_application_to_enrollment_pct": overall_conversion_pct,
            "source_attribution": inquiry_sources[:10],
            "action_queue": action_queue[:6],
            "campaigns": campaign_snapshots,
            "market_intelligence": {
                "status": "not_configured",
                "message": (
                    "External demographic, drive-time, church, preschool, competitor, "
                    "and advertising-spend datasets are not yet configured for this school."
                ),
            },
            "advertising": {
                "status": "not_configured",
                "message": (
                    "Advertising spend, impressions, clicks, and campaign cost attribution "
                    "require an approved campaign-data integration."
                ),
            },
            "snapshot_date": _today(),
            "_meta": {
                "source": "live",
                "scope": "tenant",
                "provenance": "applications.Application, applications.Applicant, applications.ApplicationEvent",
            },
        }
    )


@require_http_methods(["GET"])
@require_permission("spiritual_life.view")
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
@require_permission("office.view")
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


@require_http_methods(["GET"])
@require_permission("health.view")
def health_metrics(request):
    """Health / Nurse dashboard — daily visits, medications, immunization compliance."""
    return JsonResponse({
        "visits_today":            14,
        "meds_administered":        9,
        "immunizations_missing":    6,
        "incident_reports_week":    2,
        "todays_visits": [
            {"name": "Elijah Turner",  "grade": "9",  "reason": "Headache",          "time": "8:12 AM",  "disposition": "Sent home"},
            {"name": "Sofia Medina",   "grade": "11", "reason": "Stomach ache",      "time": "9:45 AM",  "disposition": "Returned to class"},
            {"name": "Marcus Brown",   "grade": "7",  "reason": "Inhaler (asthma)",  "time": "10:30 AM", "disposition": "Returned to class"},
            {"name": "Ava Chen",       "grade": "10", "reason": "Ankle twist",       "time": "11:05 AM", "disposition": "Ice + rest period"},
            {"name": "Noah Williams",  "grade": "8",  "reason": "Medication pickup", "time": "12:00 PM", "disposition": "Completed"},
        ],
        "medication_log": [
            {"medication": "Albuterol inhaler", "students": 3, "doses_given": 3},
            {"medication": "EpiPen (on file)",  "students": 1, "doses_given": 0},
            {"medication": "ADHD daily med",    "students": 4, "doses_given": 4},
            {"medication": "Insulin injection", "students": 1, "doses_given": 1},
        ],
        "immunization_compliance": [
            {"grade": "Grade 7",  "compliant": 24, "missing": 2},
            {"grade": "Grade 8",  "compliant": 26, "missing": 1},
            {"grade": "Grade 9",  "compliant": 28, "missing": 1},
            {"grade": "Grade 10", "compliant": 25, "missing": 2},
            {"grade": "Grade 11", "compliant": 27, "missing": 0},
            {"grade": "Grade 12", "compliant": 23, "missing": 0},
        ],
        "alerts": [
            {"label": "2 student physicals expire this month",               "severity": "yellow"},
            {"label": "6 immunization records incomplete",                   "severity": "red"},
            {"label": "1 pending parent callback — Sofia Medina",            "severity": "yellow"},
            {"label": "Inhaler stock — refill needed this week",             "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("counseling.view")
def counseling_metrics(request):
    """Counseling / Discipline dashboard — referrals, plans, detentions, caseload."""
    return JsonResponse({
        "referrals_this_week":  11,
        "active_plans":          8,
        "detentions_week":       5,
        "suspensions_week":      1,
        "recent_referrals": [
            {"student": "Marcus Brown",  "grade": "8",  "category": "Disruptive behavior", "date": "Feb 22", "counselor": "J. Okafor", "status": "open"},
            {"student": "Tyler Green",   "grade": "10", "category": "Truancy",             "date": "Feb 21", "counselor": "M. Cruz",   "status": "open"},
            {"student": "Aisha Patel",   "grade": "9",  "category": "Academic concern",    "date": "Feb 20", "counselor": "J. Okafor", "status": "plan_active"},
            {"student": "Noah Williams", "grade": "7",  "category": "Bullying",            "date": "Feb 19", "counselor": "M. Cruz",   "status": "resolved"},
            {"student": "Chloe Rivera",  "grade": "11", "category": "Anxiety / wellness",  "date": "Feb 18", "counselor": "J. Okafor", "status": "plan_active"},
        ],
        "behavior_categories": [
            {"category": "Disruptive behavior", "count": 4},
            {"category": "Truancy / late",      "count": 3},
            {"category": "Academic concern",    "count": 2},
            {"category": "Bullying",            "count": 1},
            {"category": "Wellness / anxiety",  "count": 1},
        ],
        "caseload_by_counselor": [
            {"counselor": "J. Okafor", "open": 4, "plan_active": 3, "resolved_mtd": 7},
            {"counselor": "M. Cruz",   "open": 3, "plan_active": 2, "resolved_mtd": 5},
        ],
        "alerts": [
            {"label": "2 follow-up meetings overdue this week",                      "severity": "red"},
            {"label": "Tyler Green — 3rd truancy, parent meeting needed",            "severity": "red"},
            {"label": "Repeat incident: Marcus Brown — 2nd referral in 5 days",     "severity": "yellow"},
            {"label": "1 suspension pending VP review",                              "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("food.view")
def food_metrics(request):
    """Food Services dashboard — meals, inventory, participation, payments."""
    return JsonResponse({
        "meals_served_today":      287,
        "free_reduced_count":       62,
        "inventory_low_items":       4,
        "payments_pending_count":   18,
        "menu_today": [
            {"item": "Grilled Chicken Sandwich", "category": "Entree",   "allergens": "Gluten"},
            {"item": "Caesar Salad",             "category": "Side",     "allergens": "Dairy, Egg"},
            {"item": "Apple Slices",             "category": "Fruit",    "allergens": "None"},
            {"item": "Chocolate Milk",           "category": "Beverage", "allergens": "Dairy"},
        ],
        "menu_tomorrow": [
            {"item": "Beef Tacos",    "category": "Entree",   "allergens": "Gluten, Dairy"},
            {"item": "Corn",          "category": "Side",     "allergens": "None"},
            {"item": "Orange Wedges", "category": "Fruit",    "allergens": "None"},
            {"item": "2% White Milk", "category": "Beverage", "allergens": "Dairy"},
        ],
        "inventory_low": [
            {"item": "Whole wheat buns",  "stock": "2 cases",  "reorder_level": "5 cases",  "severity": "red"},
            {"item": "Chocolate milk",    "stock": "48 units", "reorder_level": "72 units", "severity": "yellow"},
            {"item": "Apple sauce cups",  "stock": "24 units", "reorder_level": "48 units", "severity": "yellow"},
            {"item": "Latex gloves (M)",  "stock": "1 box",    "reorder_level": "3 boxes",  "severity": "red"},
        ],
        "participation_trend": [
            {"label": "Mon", "count": 274},
            {"label": "Tue", "count": 281},
            {"label": "Wed", "count": 290},
            {"label": "Thu", "count": 287},
        ],
        "alerts": [
            {"label": "2 inventory items critically low — reorder immediately",      "severity": "red"},
            {"label": "18 unpaid lunch balances — $342 aggregate outstanding",       "severity": "yellow"},
            {"label": "Free/reduced renewals due for 8 students (April)",            "severity": "yellow"},
            {"label": "Chocolate milk delivery delayed — contact vendor",            "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("athletics.view")
def athletics_metrics(request):
    """Athletic Director dashboard — events, eligibility, injuries, transport."""
    return JsonResponse({
        "upcoming_events":       6,
        "eligibility_issues":    3,
        "injuries_count":        2,
        "transportation_needs":  4,
        "week_schedule": [
            {"sport": "Boys Basketball", "opponent": "Westside Prep",    "date": "Feb 22", "time": "4:00 PM",  "home": True},
            {"sport": "Girls Soccer",    "opponent": "Eastview Academy", "date": "Feb 23", "time": "10:00 AM", "home": False},
            {"sport": "Track & Field",   "opponent": "Invitational",     "date": "Feb 24", "time": "8:00 AM",  "home": False},
            {"sport": "Boys Soccer",     "opponent": "Hillside School",  "date": "Feb 25", "time": "4:30 PM",  "home": True},
            {"sport": "Swimming",        "opponent": "State Qualifier",  "date": "Feb 26", "time": "9:00 AM",  "home": False},
        ],
        "eligibility_watch": [
            {"sport": "Boys Basketball", "count": 1, "issue": "GPA below 2.0"},
            {"sport": "Football",        "count": 1, "issue": "Missing physical"},
            {"sport": "Track & Field",   "count": 1, "issue": "Missing consent form"},
        ],
        "roster_compliance": [
            {"sport": "Boys Basketball", "roster": 12, "forms_complete": 11, "physicals_ok": 12},
            {"sport": "Girls Soccer",    "roster": 16, "forms_complete": 16, "physicals_ok": 15},
            {"sport": "Track & Field",   "roster": 22, "forms_complete": 21, "physicals_ok": 22},
            {"sport": "Swimming",        "roster": 14, "forms_complete": 14, "physicals_ok": 14},
        ],
        "alerts": [
            {"label": "1 eligibility hold — Boys Basketball may be short Saturday", "severity": "red"},
            {"label": "Missing physical: Girls Soccer — Mia Torres",               "severity": "yellow"},
            {"label": "Track consent form missing — deadline Feb 23",              "severity": "yellow"},
            {"label": "4 away game transport requests need driver confirmation",    "severity": "yellow"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("advancement.view")
def advancement_metrics(request):
    """Advancement / Fundraising dashboard — donors, campaigns, pledges, stewardship."""
    return JsonResponse({
        "donors_active":          127,
        "campaign_progress_pct":   64,
        "pledges_outstanding":     23,
        "thankyous_due":            9,
        "campaigns": [
            {"name": "Annual Fund 2026",      "goal": 150000, "raised": 96000,  "donors": 87, "status": "active"},
            {"name": "Capital Campaign",      "goal": 500000, "raised": 212000, "donors": 44, "status": "active"},
            {"name": "Scholarship Endowment", "goal": 75000,  "raised": 74800,  "donors": 38, "status": "closing"},
            {"name": "Spring Gala 2026",      "goal": 40000,  "raised": 4800,   "donors": 12, "status": "upcoming"},
        ],
        "top_sources": [
            {"source": "Alumni",           "amount": 48200},
            {"source": "Current Families", "amount": 62400},
            {"source": "Foundations",      "amount": 32000},
            {"source": "Corporate",        "amount": 19800},
            {"source": "Board",            "amount": 15000},
        ],
        "tasks": [
            {"task": "Thank-you notes — Annual Fund (Feb batch)",      "due": "Feb 23", "priority": "high"},
            {"task": "Pledge follow-up call list — 5 lapsed donors",  "due": "Feb 25", "priority": "high"},
            {"task": "Board solicitation packets prepared",            "due": "Feb 28", "priority": "normal"},
            {"task": "Matching-gift deadline — Johnson Foundation",    "due": "Mar 1",  "priority": "high"},
            {"task": "Stewardship report — Capital Campaign Q1",       "due": "Mar 7",  "priority": "normal"},
        ],
        "alerts": [
            {"label": "9 thank-you notes overdue — 5+ days since gift received",    "severity": "red"},
            {"label": "Johnson Foundation matching-gift deadline Mar 1",             "severity": "yellow"},
            {"label": "23 open pledges outstanding",                                 "severity": "yellow"},
            {"label": "Scholarship Endowment nearly closed — final push oppty",     "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("transportation.view")
def transportation_metrics(request):
    """Transportation dashboard — routes, riders, late runs, maintenance."""
    return JsonResponse({
        "routes_today":       8,
        "riders_today":     214,
        "late_runs":          1,
        "maintenance_flags":  2,
        "route_status": [
            {"route": "Route 1 — Northside", "driver": "R. Davis",    "status": "on_time", "riders": 28},
            {"route": "Route 2 — Eastview",  "driver": "T. Johnson",  "status": "on_time", "riders": 31},
            {"route": "Route 3 — Southgate", "driver": "M. Lee",      "status": "late",    "riders": 25},
            {"route": "Route 4 — Westpark",  "driver": "A. Martinez", "status": "on_time", "riders": 27},
            {"route": "Route 5 — Central",   "driver": "S. Clark",    "status": "on_time", "riders": 22},
            {"route": "Route 6 — Hillcrest", "driver": "B. Walker",   "status": "on_time", "riders": 26},
            {"route": "Route 7 — Valley Rd", "driver": "C. Hall",     "status": "on_time", "riders": 29},
            {"route": "Route 8 — Sports/AM", "driver": "D. Young",    "status": "on_time", "riders": 26},
        ],
        "incidents": [
            {"date": "Feb 20", "route": "Route 3", "description": "Minor delay — traffic accident on Oak Ave", "resolved": True},
            {"date": "Feb 18", "route": "Route 5", "description": "Bus #14 fuel sensor warning — resolved at depot", "resolved": True},
        ],
        "alerts": [
            {"label": "Route 3 running 12 min late — parents notified",        "severity": "yellow"},
            {"label": "Bus #11 — oil change overdue (2,200 mi past schedule)", "severity": "red"},
            {"label": "Bus #7 — tire inspection due this week",                "severity": "yellow"},
            {"label": "Substitute driver needed for Route 2 on Feb 27",       "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("facilities.view")
def facilities_metrics(request):
    """Facilities dashboard — work orders, SLA, PM calendar, vendor visits."""
    return JsonResponse({
        "work_orders_open":        12,
        "sla_breaches":             2,
        "inspections_due":          3,
        "vendor_visits_this_week":  4,
        "open_work_orders": [
            {"id": "WO-2201", "location": "Gym — HVAC",        "description": "Cooling unit failure", "priority": "high",   "days_open": 3,  "assigned": "M. Torres"},
            {"id": "WO-2198", "location": "Library",           "description": "Ceiling tile leak",   "priority": "high",   "days_open": 5,  "assigned": "J. Reyes"},
            {"id": "WO-2195", "location": "Cafeteria kitchen", "description": "Hood vent cleaning",  "priority": "normal", "days_open": 8,  "assigned": "M. Torres"},
            {"id": "WO-2193", "location": "Admin — B Wing",   "description": "LED retrofit",        "priority": "low",    "days_open": 12, "assigned": "J. Reyes"},
            {"id": "WO-2190", "location": "Parking lot",      "description": "Line repainting",     "priority": "low",    "days_open": 14, "assigned": "TBD"},
        ],
        "pm_calendar": [
            {"task": "Fire extinguisher inspection",   "due": "Feb 28", "status": "scheduled"},
            {"task": "Emergency lighting test",        "due": "Feb 28", "status": "scheduled"},
            {"task": "Roof inspection (spring)",       "due": "Mar 15", "status": "planned"},
            {"task": "HVAC filter replacement — all", "due": "Mar 20", "status": "planned"},
            {"task": "Elevator annual certification",  "due": "Apr 1",  "status": "planned"},
        ],
        "top_categories": [
            {"category": "HVAC / Mechanical", "count": 4},
            {"category": "Plumbing",          "count": 3},
            {"category": "Electrical",        "count": 2},
            {"category": "General Repairs",   "count": 2},
            {"category": "Grounds",           "count": 1},
        ],
        "alerts": [
            {"label": "WO-2198 — Library ceiling leak: SLA breach (day 5, SLA=3)", "severity": "red"},
            {"label": "WO-2201 — Gym HVAC: SLA breach, affecting PE classes",      "severity": "red"},
            {"label": "3 PM inspections due before March 1",                       "severity": "yellow"},
            {"label": "Elevator inspection 40 days out — schedule vendor",         "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("security.view")
def security_metrics(request):
    """Security / Safety dashboard — drills, incidents, access exceptions, cameras."""
    return JsonResponse({
        "drills_completed_ytd":   4,
        "incidents_week":         1,
        "door_access_exceptions": 3,
        "camera_uptime_pct":     98,
        "incident_log": [
            {"date": "Feb 21", "type": "Unauthorized entry attempt", "location": "South entrance", "severity": "medium", "status": "resolved"},
            {"date": "Feb 14", "type": "After-hours access",         "location": "Gym side door",  "severity": "low",    "status": "resolved"},
            {"date": "Jan 30", "type": "Visitor badge violation",    "location": "Admin lobby",    "severity": "low",    "status": "resolved"},
        ],
        "drill_schedule": [
            {"drill": "Fire Drill",        "date": "Mar 5",  "status": "scheduled", "required": True},
            {"drill": "Lockdown (ALICE)",  "date": "Mar 19", "status": "scheduled", "required": True},
            {"drill": "Shelter-in-Place", "date": "Apr 9",  "status": "planned",   "required": True},
            {"drill": "Evacuation (full)", "date": "Apr 23", "status": "planned",   "required": True},
        ],
        "open_issues": [
            {"issue": "Camera #7 — Main Hall (west): offline 2 days", "severity": "red"},
            {"issue": "Fob access log: 2 unknown badge scans Feb 22", "severity": "yellow"},
            {"issue": "South gate key pad battery low",               "severity": "yellow"},
        ],
        "alerts": [
            {"label": "Camera #7 offline — main hall west blind spot",        "severity": "red"},
            {"label": "3 door access exceptions logged — review required",    "severity": "yellow"},
            {"label": "Next required drill Mar 5 — logistics not confirmed",    "severity": "yellow"},
            {"label": "Annual safety checklist review due March 31",           "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("academic_support.view")
def academic_support_metrics(request):
    """Academic Support / SPED dashboard — IEPs, accommodations, caseload.
    Privacy rule: all student references use opaque IDs, never names."""
    return JsonResponse({
        "students_on_iep":       47,
        "upcoming_reviews":      9,
        "accommodations_active": 112,
        "referrals_pending":     4,
        "iep_reviews": [
            {"student_id": "STU-0441", "type": "Annual Review",    "due_date": "Mar 4",  "status": "pending"},
            {"student_id": "STU-0221", "type": "Re-evaluation",    "due_date": "Mar 11", "status": "in_progress"},
            {"student_id": "STU-0388", "type": "Annual Review",    "due_date": "Mar 18", "status": "pending"},
            {"student_id": "STU-0092", "type": "Initial Eval",     "due_date": "Mar 25", "status": "pending"},
            {"student_id": "STU-0567", "type": "504 Update",       "due_date": "Apr 1",  "status": "pending"},
        ],
        "accommodations_by_grade": [
            {"grade": "K",  "count": 8,  "pct": 32},
            {"grade": "1",  "count": 11, "pct": 44},
            {"grade": "2",  "count": 14, "pct": 56},
            {"grade": "3",  "count": 12, "pct": 48},
            {"grade": "4",  "count": 18, "pct": 72},
            {"grade": "5",  "count": 15, "pct": 60},
            {"grade": "6",  "count": 9,  "pct": 36},
            {"grade": "7",  "count": 13, "pct": 52},
            {"grade": "8",  "count": 12, "pct": 48},
        ],
        "caseload": [
            {"specialist": "Ms. Rivera",   "active_plans": 18, "pending_reviews": 3},
            {"specialist": "Mr. Chen",     "active_plans": 15, "pending_reviews": 4},
            {"specialist": "Ms. Johnson",  "active_plans": 14, "pending_reviews": 2},
        ],
        "alerts": [
            {"label": "4 IEP annual reviews due before Mar 31 — schedule meetings",   "severity": "red"},
            {"label": "STU-0221 re-evaluation window closes Mar 11",               "severity": "yellow"},
            {"label": "Grade 4 accommodation rate 72% — verify documentation",     "severity": "yellow"},
            {"label": "2 referrals pending initial eligibility determination",     "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("fine_arts.view")
def fine_arts_metrics(request):
    """Fine Arts Director dashboard — performances, ensembles, equipment."""
    return JsonResponse({
        "enrolled_students":     186,
        "performances_this_term": 4,
        "equipment_needs":        3,
        "parent_volunteers":      22,
        "performances": [
            {"event": "Spring Arts Showcase",  "date": "Mar 14", "venue": "Main Auditorium", "status": "confirmed"},
            {"event": "Band Concert",          "date": "Apr 2",  "venue": "Main Auditorium", "status": "scheduled"},
            {"event": "Drama Production",      "date": "Apr 24", "venue": "Black Box",       "status": "scheduled"},
            {"event": "Year-End Recital",      "date": "May 19", "venue": "Main Auditorium", "status": "pending"},
        ],
        "ensembles": [
            {"name": "Concert Band",       "students": 48, "pct": 80},
            {"name": "Choir",              "students": 62, "pct": 100},
            {"name": "Orchestra",          "students": 31, "pct": 52},
            {"name": "Drama Club",         "students": 28, "pct": 47},
            {"name": "Visual Arts Studio", "students": 17, "pct": 28},
        ],
        "equipment_list": [
            {"item": "Trombone (replacement)",   "qty": 2, "est_cost": "$1,200", "priority": "high"},
            {"item": "Art supply restock",       "qty": 1, "est_cost": "$340",   "priority": "medium"},
            {"item": "Microphone stand set",     "qty": 4, "est_cost": "$200",   "priority": "low"},
        ],
        "alerts": [
            {"label": "Spring Arts Showcase venue contract unsigned — due Feb 28",  "severity": "red"},
            {"label": "2 replacement trombones needed before Mar 14 concert",    "severity": "yellow"},
            {"label": "Parent volunteer sign-up open for Apr 2 concert",         "severity": "gray"},
            {"label": "Year-End Recital budget request due Apr 1",               "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("library.view")
def library_metrics(request):
    """Library / Media Center dashboard — circulation, collection, digital resources."""
    return JsonResponse({
        "books_checked_out":       248,
        "overdue_items":           17,
        "new_materials_this_month": 34,
        "digital_resources_active": 6,
        "overdue_list": [
            {"borrower_id": "B-0441", "title": "The Giver",            "due_date": "Feb 8",  "days_overdue": 14},
            {"borrower_id": "B-0092", "title": "Hatchet",             "due_date": "Feb 12", "days_overdue": 10},
            {"borrower_id": "B-0388", "title": "Number the Stars",    "due_date": "Feb 15", "days_overdue":  7},
            {"borrower_id": "B-0221", "title": "Charlotte's Web",     "due_date": "Feb 18", "days_overdue":  4},
            {"borrower_id": "B-0567", "title": "Bridge to Terabithia","due_date": "Feb 19", "days_overdue":  3},
        ],
        "collection_by_category": [
            {"category": "Fiction",        "count": 4200, "pct": 100},
            {"category": "Non-Fiction",    "count": 2800, "pct": 67},
            {"category": "Reference",      "count": 640,  "pct": 15},
            {"category": "Graphic Novels", "count": 310,  "pct": 7},
            {"category": "Periodicals",    "count": 85,   "pct": 2},
        ],
        "digital_resources": [
            {"name": "Sora (eBooks)",         "licenses": 200, "usage_mtd": 142},
            {"name": "encyclopedia Britannica","licenses":  50, "usage_mtd":  38},
            {"name": "PebbleGo",              "licenses": 100, "usage_mtd":  87},
            {"name": "Newsela",               "licenses": 300, "usage_mtd": 211},
            {"name": "Follett Destiny",        "licenses":   1, "usage_mtd": "N/A"},
            {"name": "Khan Academy",           "licenses": 500, "usage_mtd": 388},
        ],
        "alerts": [
            {"label": "17 overdue items — 2 exceed 14 days",                "severity": "red"},
            {"label": "Sora license utilization at 71% — consider expansion","severity": "yellow"},
            {"label": "34 new materials catalogued this month",             "severity": "gray"},
            {"label": "Annual weeding review scheduled for April",          "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("extended_care.view")
def extended_care_metrics(request):
    """Extended Care / Aftercare dashboard — roster, staff, trends.
    Privacy rule: show aggregate program counts only, no student names."""
    return JsonResponse({
        "enrolled_today":   74,
        "staff_ratio":      "1:8",
        "incidents_week":    1,
        "invoices_pending": 12,
        "roster_summary": [
            {"program": "AM Care (7:00–8:00)",    "enrolled": 18, "present": 16, "late_pickup": 0},
            {"program": "PM Care (3:00–5:00)",    "enrolled": 42, "present": 39, "late_pickup": 2},
            {"program": "PM Care (5:00–6:00)",    "enrolled": 14, "present": 12, "late_pickup": 1},
        ],
        "staff_schedule": [
            {"name": "T. Williams",  "shift": "7:00–9:00 AM",  "program": "AM Care",   "status": "present"},
            {"name": "L. Garcia",    "shift": "2:30–5:30 PM",  "program": "PM Care",   "status": "present"},
            {"name": "R. Thompson",  "shift": "2:30–6:00 PM",  "program": "PM Care",   "status": "present"},
            {"name": "M. Patel",     "shift": "4:30–6:00 PM",  "program": "PM Late",   "status": "present"},
        ],
        "weekly_trend": [
            {"day": "Monday",    "count": 68, "pct": 92},
            {"day": "Tuesday",   "count": 71, "pct": 96},
            {"day": "Wednesday", "count": 74, "pct": 100},
            {"day": "Thursday",  "count": 70, "pct": 95},
            {"day": "Friday",    "count": 52, "pct": 70},
        ],
        "alerts": [
            {"label": "2 late pickups today — guardian contact required by 6:15 PM", "severity": "yellow"},
            {"label": "12 unpaid invoices for Feb — billing reminder due",           "severity": "yellow"},
            {"label": "Staff:child ratio compliant across all programs",              "severity": "gray"},
            {"label": "Spring break coverage plan due March 1",                       "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("registrar.view")
def registrar_metrics(request):
    """Registrar / Records dashboard — enrollment, requests, transcripts, holds."""
    return JsonResponse({
        "enrollment_total":       412,
        "pending_requests":         8,
        "transcripts_issued_mtd":  23,
        "holds_active":             3,
        "pending_requests_list": [
            {"type": "Records Transfer",   "submitted": "Feb 18", "target_date": "Feb 28", "status": "in_progress"},
            {"type": "Transcript Request", "submitted": "Feb 19", "target_date": "Feb 26", "status": "pending"},
            {"type": "Enrollment Verify",  "submitted": "Feb 20", "target_date": "Feb 27", "status": "pending"},
            {"type": "Records Transfer",   "submitted": "Feb 21", "target_date": "Mar 3",  "status": "hold"},
            {"type": "Transcript Request", "submitted": "Feb 22", "target_date": "Feb 29", "status": "pending"},
        ],
        "transcript_queue": [
            {"destination_type": "High School",   "count": 9,  "avg_days": 3.2},
            {"destination_type": "College",       "count": 6,  "avg_days": 4.1},
            {"destination_type": "Transfer",      "count": 5,  "avg_days": 2.9},
            {"destination_type": "Other",         "count": 3,  "avg_days": 5.0},
        ],
        "new_enrollments_by_grade": [
            {"grade": "K",  "count": 4, "pct": 80},
            {"grade": "1",  "count": 2, "pct": 40},
            {"grade": "3",  "count": 1, "pct": 20},
            {"grade": "5",  "count": 3, "pct": 60},
            {"grade": "7",  "count": 1, "pct": 20},
            {"grade": "8",  "count": 2, "pct": 40},
        ],
        "alerts": [
            {"label": "3 enrollment holds require admin clearance before records release","severity": "red"},
            {"label": "5 pending requests unacknowledged for 3+ days",                  "severity": "yellow"},
            {"label": "23 transcripts issued MTD — on pace",                            "severity": "gray"},
            {"label": "Year-end enrollment census due April 15",                        "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("communications.view")
def communications_metrics(request):
    """Communications Director dashboard — campaigns, engagement, announcements."""
    return JsonResponse({
        "messages_sent_week":       1840,
        "open_rate_pct":             64,
        "announcements_scheduled":    5,
        "unsubscribes_week":           3,
        "campaigns": [
            {"name": "Feb Newsletter",        "sent": "Feb 14", "open_rate": "68%", "status": "sent"},
            {"name": "Spring Break Reminder", "sent": "Feb 21", "open_rate": "72%", "status": "sent"},
            {"name": "March Events Digest",   "sent": "Mar 1",  "open_rate": "—",    "status": "scheduled"},
            {"name": "Fundraiser Kickoff",    "sent": "TBD",    "open_rate": "—",    "status": "draft"},
        ],
        "channel_engagement": [
            {"channel": "Email",       "open_rate": "64%", "pct": 64},
            {"channel": "Push (App)",  "open_rate": "41%", "pct": 41},
            {"channel": "SMS",         "open_rate": "89%", "pct": 89},
            {"channel": "Web Banner",  "open_rate": "22%", "pct": 22},
        ],
        "upcoming_announcements": [
            {"subject": "Spring Break Schedule",  "audience": "All Families",     "scheduled": "Feb 28",  "status": "scheduled"},
            {"subject": "March Hot Lunch Menu",   "audience": "All Families",     "scheduled": "Mar 1",   "status": "scheduled"},
            {"subject": "Teacher Appreciation",  "audience": "Parent Group",     "scheduled": "Mar 10",  "status": "scheduled"},
            {"subject": "Board Meeting Reminder","audience": "Board Members",    "scheduled": "Mar 14",  "status": "scheduled"},
            {"subject": "Fundraiser Launch",      "audience": "All Families",     "scheduled": "TBD",     "status": "draft"},
        ],
        "alerts": [
            {"label": "Fundraiser Kickoff campaign content missing — due Feb 28",       "severity": "red"},
            {"label": "3 unsubscribes this week — monitor deliverability",             "severity": "yellow"},
            {"label": "SMS engagement at 89% — consider SMS-first for urgent comms",  "severity": "gray"},
            {"label": "App push notification opt-in rate below 50%",                  "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("pd.view")
def pd_metrics(request):
    """PD / Staff Development dashboard — sessions, certifications, completion."""
    return JsonResponse({
        "sessions_this_month":      6,
        "staff_hours_logged":      142,
        "certifications_expiring":   4,
        "satisfaction_avg":         4.3,
        "upcoming_sessions": [
            {"title": "Differentiated Instruction",   "date": "Mar 4",  "facilitator": "Dr. Kim",     "registered": 24, "status": "upcoming"},
            {"title": "Restorative Practices",        "date": "Mar 11", "facilitator": "Ms. Torres",  "registered": 18, "status": "upcoming"},
            {"title": "Data-Driven Instruction",      "date": "Mar 18", "facilitator": "Mr. Hayes",   "registered": 21, "status": "upcoming"},
            {"title": "Google Workspace Advanced",    "date": "Mar 25", "facilitator": "Tech Team",   "registered":  9, "status": "upcoming"},
        ],
        "certifications": [
            {"name": "First Aid / CPR",           "staff_count": 38, "expiring_90d": 4},
            {"name": "Mandated Reporter",          "staff_count": 42, "expiring_90d": 0},
            {"name": "Safe Environment (VIRTUS)",  "staff_count": 42, "expiring_90d": 2},
            {"name": "ALICE / Safety Training",   "staff_count": 40, "expiring_90d": 1},
        ],
        "completion_by_dept": [
            {"dept": "Elementary",   "pct": 92},
            {"dept": "Middle School","pct": 84},
            {"dept": "Specials",     "pct": 78},
            {"dept": "Support Staff","pct": 71},
            {"dept": "Admin",        "pct": 100},
        ],
        "alerts": [
            {"label": "4 First Aid/CPR certifications expire within 90 days",          "severity": "red"},
            {"label": "Support Staff PD completion at 71% — below 80% target",         "severity": "yellow"},
            {"label": "2 VIRTUS renewals due Q2 — schedule sessions",                  "severity": "yellow"},
            {"label": "Overall satisfaction avg 4.3/5 across Feb sessions",            "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("student_services.view")
def student_services_metrics(request):
    """Student Services dashboard — lunch balances, applications, active services.
    Privacy rule: aggregate grade-level counts only, no individual records."""
    return JsonResponse({
        "lunch_balance_alerts":   31,
        "unpaid_balances_total": 1140,
        "applications_pending":    7,
        "services_active":        89,
        "balance_alerts_by_grade": [
            {"grade": "K",  "below_five": 3, "at_zero": 1, "severity": "warning"},
            {"grade": "1",  "below_five": 4, "at_zero": 2, "severity": "critical"},
            {"grade": "2",  "below_five": 5, "at_zero": 1, "severity": "warning"},
            {"grade": "3",  "below_five": 2, "at_zero": 0, "severity": "info"},
            {"grade": "4",  "below_five": 4, "at_zero": 1, "severity": "warning"},
            {"grade": "5",  "below_five": 3, "at_zero": 0, "severity": "info"},
            {"grade": "6",  "below_five": 4, "at_zero": 2, "severity": "critical"},
            {"grade": "7",  "below_five": 3, "at_zero": 1, "severity": "warning"},
            {"grade": "8",  "below_five": 3, "at_zero": 1, "severity": "warning"},
        ],
        "services_by_type": [
            {"type": "Free / Reduced Lunch",    "count": 48, "pct": 100},
            {"type": "Before Care Subsidy",     "count": 12, "pct": 25},
            {"type": "Tutoring Support",        "count": 19, "pct": 40},
            {"type": "Uniform Assistance",      "count": 10, "pct": 21},
        ],
        "pending_applications": [
            {"service_type": "Free Lunch",       "count": 3, "oldest_days": 5},
            {"service_type": "Reduced Lunch",    "count": 2, "oldest_days": 12},
            {"service_type": "Before Care Sub.","count": 1, "oldest_days": 8},
            {"service_type": "Uniform Assist.", "count": 1, "oldest_days": 3},
        ],
        "alerts": [
            {"label": "2 Free/Reduced Lunch applications unreviewed for 12+ days",       "severity": "red"},
            {"label": "Grade 1 + Grade 6 have 2 zero-balance accounts each",             "severity": "yellow"},
            {"label": "31 accounts below $5 — automated reminder batch queued",          "severity": "yellow"},
            {"label": "7 open service applications pending review",                       "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })


@require_http_methods(["GET"])
@require_permission("volunteer_management.view")
def volunteer_management_metrics(request):
    """Volunteer Management dashboard metrics."""
    get_request_school_id(request, required=True)
    return JsonResponse({
        "total_hours_logged": 1248.5,
        "pending_approvals": 12,
        "active_volunteers": 87,
        "open_slots": 17,
        "background_checks_expiring": 16,
        "volunteer_categories": [
            {"category": "Classroom Help", "volunteers": 34, "hours_ytd": 412},
            {"category": "Event Support", "volunteers": 28, "hours_ytd": 318},
        ],
        "upcoming_opportunities": [
            {"event": "Spring Fair Setup", "date": "Apr 12", "slots_needed": 8, "filled": 3},
            {"event": "Graduation Reception", "date": "May 23", "slots_needed": 12, "filled": 4},
        ],
        "alerts": [
            {"label": "Background checks expiring in 30 days", "severity": "red"},
            {"label": "Pending service-hour approvals require review", "severity": "yellow"},
        ],
        "snapshot_date": _today(),
        "_meta": {"source": "fallback"},
    })


@require_http_methods(["GET"])
@require_permission("alumni.view")
def alumni_metrics(request):
    """Alumni Relations dashboard metrics."""
    get_request_school_id(request, required=True)
    return JsonResponse({
        "total_alumni": 847,
        "total_cohorts": 12,
        "engaged_alumni": 312,
        "email_bounces": 342,
        "donations_this_year": 18400,
        "cohorts": [
            {"year": "Class of 2023", "members": 78, "engaged": 45, "donated": 12},
            {"year": "Class of 2022", "members": 82, "engaged": 51, "donated": 18},
        ],
        "upcoming_events": [
            {"event": "Alumni Networking Night", "date": "Apr 10", "rsvp": 34, "capacity": 60},
        ],
        "alerts": [
            {"label": "High alumni email bounce count", "severity": "yellow"},
        ],
        "snapshot_date": _today(),
        "_meta": {"source": "fallback"},
    })


@require_http_methods(["GET"])
@require_permission("network_benchmarking.view")
def network_benchmarking_metrics(request):
    """Network Benchmarking dashboard metrics."""
    get_request_school_id(request, required=True)
    return JsonResponse({
        "schools_in_network": 47,
        "avg_network_score": 81,
        "benchmarks_met": 34,
        "benchmarks_total": 48,
        "improvement_plans": 14,
        "benchmark_categories": [
            {"category": "Academic Performance", "met": 9, "total": 12, "pct": 75},
            {"category": "Financial Health", "met": 4, "total": 8, "pct": 50},
        ],
        "school_performance": [
            {"school": "Heritage Christian Academy", "score": 84, "quartile": 1, "benchmarks_met": 40},
        ],
        "trend": [
            {"quarter": "Q1", "avg_score": 76},
            {"quarter": "Q2", "avg_score": 78},
            {"quarter": "Q3", "avg_score": 81},
        ],
        "alerts": [
            {"label": "Financial Health benchmark below target", "severity": "red"},
        ],
        "snapshot_date": _today(),
        "_meta": {"source": "fallback"},
    })


@require_http_methods(["GET"])
@require_permission("platform_ops.view")
def platform_ops_metrics(request):
    """Platform Operations dashboard metrics."""
    get_request_school_id(request, required=True)
    return JsonResponse({
        "provisioning_jobs_running": 0,
        "provisioning_jobs_failed": 1,
        "provisioning_jobs_succeeded": 143,
        "active_tenants": 47,
        "audit_events_7d": 28,
        "system_health": "operational",
        "provisioning_queue": [
            {"school": "Westview Academy", "state": "running", "progress": 64, "submitted": "Today 7:50 AM"},
        ],
        "health_checks": [
            {"check": "Database connectivity", "status": "pass", "latency_ms": 4},
            {"check": "Email delivery", "status": "warn", "latency_ms": 210},
        ],
        "alerts": [
            {"label": "Provisioning failures require review", "severity": "red"},
        ],
        "snapshot_date": _today(),
        "_meta": {"source": "fallback"},
    })
