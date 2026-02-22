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


@require_http_methods(["GET"])
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
            {"label": "Next required drill Mar 5 — logistics not confirmed",  "severity": "yellow"},
            {"label": "Annual safety checklist review due March 31",          "severity": "gray"},
        ],
        "snapshot_date": _today(),
    })
