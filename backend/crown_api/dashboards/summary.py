"""
Dashboard summary service — builds role-specific widget payloads.

Phase A: aggregates from live DB where cheaply available; graceful stubs
         for data that requires heavier joins (Phase B will replace stubs).

Rules:
- Each widget has a STABLE key (never rename after shipping).
- Priority is a sort order: lower = appears earlier in the grid.
- All DB queries are scoped to school_id (tenant safety).
- Errors in any widget fall back to a stub — never break the whole dashboard.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Per-widget data builders — each returns the "data" dict for its widget.
# ---------------------------------------------------------------------------

def _quick_actions(role: str) -> dict:
    """Role-appropriate fast-jump links."""
    actions_by_role = {
        "teacher": [
            {"label": "Take attendance", "to": "/teacher/attendance"},
            {"label": "Grade submissions", "to": "/academics"},
            {"label": "Message a family", "to": "/comms/compose"},
        ],
        "parent": [
            {"label": "View child's grades", "to": "/parent"},
            {"label": "View attendance", "to": "/parent/attendance"},
            {"label": "Message staff", "to": "/comms/compose"},
            {"label": "View balance", "to": "/billing"},
        ],
        "student": [
            {"label": "My grades", "to": "/student"},
            {"label": "Upcoming assignments", "to": "/student"},
            {"label": "My schedule", "to": "/schedule"},
        ],
        "finance": [
            {"label": "View unpaid balances", "to": "/finance"},
            {"label": "Process invoices", "to": "/finance"},
            {"label": "Payment history", "to": "/finance"},
        ],
        "registrar": [
            {"label": "Enrollment management", "to": "/registrar"},
            {"label": "Transcripts", "to": "/transcript"},
            {"label": "Schedule builder", "to": "/academics"},
        ],
    }
    default_actions = [
        {"label": "Message a family", "to": "/comms/compose"},
        {"label": "View unpaid balances", "to": "/finance"},
        {"label": "Check missing work", "to": "/academics"},
        {"label": "Run attendance report", "to": "/teacher/attendance"},
    ]
    return {"actions": actions_by_role.get(role, default_actions)}


def _alerts_flip(school_id: str) -> dict:
    """
    Phase A stub — counts + next-step items.
    Phase B: wire to real attendance-risk, AR, and missing-work queries.
    """
    return {
        "front": {"good": 12, "warn": 4, "bad": 1},
        "back": {
            "items": [
                {"level": "warn", "text": "2 students trending toward chronic absenteeism"},
                {"level": "bad", "text": "1 payment past due > 30 days"},
                {"level": "warn", "text": "3 missing grade submissions"},
            ]
        },
    }


def _enrollment_snapshot(school_id: str) -> dict:
    """Live enrollment count — gracefully degrades to stub."""
    try:
        from households.models import Student
        count = Student.objects.filter(school_id=school_id, is_active=True).count()
        return {"count": count, "label": "Active students"}
    except Exception:
        logger.debug("enrollment_snapshot: graceful stub (households.Student unavailable)", exc_info=True)
        return {"count": "--", "label": "Active students"}


def _sections_count(school_id: str) -> dict:
    """Live active section count."""
    try:
        from academics.models import Section
        count = Section.objects.filter(school_id=school_id).count()
        return {"count": count, "label": "Active sections"}
    except Exception:
        logger.debug("sections_count: graceful stub", exc_info=True)
        return {"count": "--", "label": "Active sections"}


def _missing_work_table(school_id: str) -> dict:
    """
    Phase A stub — top missing assignments for teacher view.
    Phase B: wire to assignments + gradebook models.
    """
    return {
        "columns": ["Student", "Course", "Missing", "Last activity"],
        "rows": [
            ["A. Carter", "Math 8", 3, "2 days ago"],
            ["J. Rivera", "Bible 8", 2, "4 days ago"],
            ["M. Chen", "ELA 8", 2, "1 day ago"],
        ],
    }


def _family_balance(school_id: str) -> dict:
    """
    Phase A stub — family balance for parent view.
    Phase B: query finance/billing models scoped to request user's household.
    """
    return {"amount": 245.75, "currency": "USD", "status": "due_soon"}


def _grades_trend(school_id: str) -> dict:
    """Phase A stub — 6-week grade trend for parent/student views."""
    return {
        "series": [
            {
                "name": "Child 1",
                "points": [
                    {"x": "W1", "y": 88}, {"x": "W2", "y": 90},
                    {"x": "W3", "y": 87}, {"x": "W4", "y": 91},
                    {"x": "W5", "y": 92}, {"x": "W6", "y": 90},
                ],
            },
        ]
    }


def _payments_this_month(school_id: str) -> dict:
    """Phase A stub for finance monthly collections widget."""
    return {"amount": 48250.00, "currency": "USD", "label": "Collected this month"}


def _ar_snapshot(school_id: str) -> dict:
    """Phase A stub for finance AR widget."""
    return {"count": 14, "total_due": 6340.00, "currency": "USD", "label": "Overdue accounts"}


def _messages_inbox(school_id: str) -> dict:
    """Phase A stub — recent comms threads."""
    return {
        "threads": [
            {"from": "Smith Family", "subject": "Homework question", "ago": "1h"},
            {"from": "Admin", "subject": "Schedule change", "ago": "3h"},
            {"from": "Rivera Family", "subject": "Absence note", "ago": "Yesterday"},
        ]
    }


def _events_upcoming(school_id: str) -> dict:
    """Phase A stub — upcoming calendar events."""
    return {
        "events": [
            {"name": "Chapel", "date": "Today, 10:00 AM"},
            {"name": "Spring Concert", "date": "Mar 15"},
            {"name": "Spring Break starts", "date": "Mar 22"},
        ]
    }


def _attendance_risk_donut(school_id: str) -> dict:
    """Phase A stub — attendance risk distribution."""
    return {
        "segments": [
            {"label": "On Track", "value": 312, "color": "good"},
            {"label": "At Risk", "value": 18, "color": "warn"},
            {"label": "Chronic", "value": 4, "color": "bad"},
        ]
    }


# ---------------------------------------------------------------------------
# Widget builders per role — returns sorted list of widget dicts.
# ---------------------------------------------------------------------------

_BASE_WIDGETS_TEMPLATE = [
    # Present for ALL roles
    {
        "key": "quick_actions",
        "type": "actions",
        "title": "Quick Actions",
        "subtitle": "Fast jumps to common tasks",
        "size": "md",
        "priority": 10,
    },
    {
        "key": "alerts_flip",
        "type": "flip",
        "title": "Today's Alerts",
        "subtitle": "Flip for next steps",
        "size": "md",
        "priority": 20,
        "drilldown": {"enabled": True, "endpoint": "/api/dashboards/drilldown/?widget=alerts_flip"},
    },
    {
        "key": "messages_inbox",
        "type": "feed",
        "title": "Messages",
        "subtitle": "Recent threads",
        "size": "md",
        "priority": 900,
        "drilldown": {"enabled": True, "endpoint": "/api/dashboards/drilldown/?widget=messages_inbox"},
    },
    {
        "key": "events_upcoming",
        "type": "feed",
        "title": "Upcoming Events",
        "size": "md",
        "priority": 910,
    },
]


def build_widgets_for_role(role: str, school_id: str) -> list[dict]:
    """Build the ordered widget list for a role, populating data fields."""

    # Shared data builders (always run)
    shared_data = {
        "quick_actions": _quick_actions(role),
        "alerts_flip": _alerts_flip(school_id),
        "messages_inbox": _messages_inbox(school_id),
        "events_upcoming": _events_upcoming(school_id),
    }

    # Start from copies of the base templates
    widgets: list[dict] = [dict(w) for w in _BASE_WIDGETS_TEMPLATE]

    # Role-specific additions
    if role in ("admin", "registrar"):
        widgets += [
            {"key": "enrollment_snapshot", "type": "stat", "title": "Enrollment",
             "size": "sm", "priority": 30, "data": _enrollment_snapshot(school_id)},
            {"key": "sections_count", "type": "stat", "title": "Active Sections",
             "size": "sm", "priority": 35, "data": _sections_count(school_id)},
            {"key": "attendance_risk", "type": "chart_donut", "title": "Attendance Risk",
             "subtitle": "This week", "size": "md", "priority": 40,
             "data": _attendance_risk_donut(school_id),
             "drilldown": {"enabled": True, "endpoint": "/api/dashboards/drilldown/?widget=attendance_risk"}},
        ]

    if role == "teacher":
        widgets += [
            {"key": "my_sections", "type": "stat", "title": "My Sections",
             "size": "sm", "priority": 30, "data": _sections_count(school_id)},
            {"key": "missing_work", "type": "table", "title": "Missing Work",
             "subtitle": "Top 10 by recency", "size": "lg", "priority": 40,
             "data": _missing_work_table(school_id),
             "drilldown": {"enabled": True, "endpoint": "/api/dashboards/drilldown/?widget=missing_work"}},
            {"key": "attendance_risk", "type": "chart_donut", "title": "Class Attendance Risk",
             "subtitle": "My students", "size": "md", "priority": 50,
             "data": _attendance_risk_donut(school_id)},
        ]

    if role == "parent":
        widgets += [
            {"key": "balances", "type": "stat", "title": "Family Balance",
             "size": "sm", "priority": 30, "data": _family_balance(school_id),
             "drilldown": {"enabled": True, "endpoint": "/api/dashboards/drilldown/?widget=balances"}},
            {"key": "grades_trend", "type": "chart_line", "title": "Grades Trend",
             "subtitle": "Last 6 weeks", "size": "lg", "priority": 40,
             "data": _grades_trend(school_id)},
        ]

    if role == "student":
        widgets += [
            {"key": "grades_trend", "type": "chart_line", "title": "My Grade Trend",
             "subtitle": "Last 6 weeks", "size": "lg", "priority": 30,
             "data": _grades_trend(school_id)},
            {"key": "missing_work", "type": "table", "title": "Missing Assignments",
             "size": "md", "priority": 40, "data": _missing_work_table(school_id)},
        ]

    if role == "finance":
        widgets += [
            {"key": "payments_this_month", "type": "stat", "title": "Payments This Month",
             "size": "sm", "priority": 30, "data": _payments_this_month(school_id)},
            {"key": "balances", "type": "stat", "title": "Overdue AR",
             "size": "sm", "priority": 35, "data": _ar_snapshot(school_id),
             "drilldown": {"enabled": True, "endpoint": "/api/dashboards/drilldown/?widget=balances"}},
        ]

    # Populate data for base widgets that don't already have it
    for w in widgets:
        if "data" not in w and w["key"] in shared_data:
            w["data"] = shared_data[w["key"]]
        elif "data" not in w:
            w["data"] = {}

    return sorted(widgets, key=lambda w: w.get("priority", 999))


def build_dashboard_summary(role: str, school_id: str) -> dict:
    return {
        "role": role,
        "school_id": str(school_id),
        "generated_at": _now_iso(),
        "widgets": build_widgets_for_role(role, str(school_id)),
    }


def build_dashboard_alerts(school_id: str) -> list[dict]:
    """
    Phase A stub alert list.
    Phase B: wire to attendance-risk, AR-overdue, and missing-grade queries.
    """
    return [
        {"key": "attendance_risk_1", "level": "warn",
         "text": "2 students trending toward chronic absenteeism",
         "action_url": "/teacher/attendance", "widget": "attendance_risk"},
        {"key": "ar_overdue_1", "level": "bad",
         "text": "1 payment past due > 30 days",
         "action_url": "/finance", "widget": "balances"},
        {"key": "missing_grades_1", "level": "warn",
         "text": "3 missing grade submissions",
         "action_url": "/academics", "widget": "missing_work"},
    ]
