from datetime import date, timedelta


def build_board_metrics_payload(*, school_id) -> dict:
    """Return the board metrics payload consumed by the existing BoardDashboard
    frontend component. Matches its expected response shape exactly.
    Replace placeholder zeros with real service calls when available."""
    return {
        "enrollment": {
            "current": 0,
            "target": 0,
            "waitlist": 0,
            "retention_pct": 0.0,
        },
        "finance_health": {
            "tuition_billed": 0.0,
            "tuition_collected": 0.0,
            "collection_pct": 0.0,
            "aid_awarded": 0.0,
            "ar_90_plus": 0.0,
        },
        "mission": {
            "survey_pulse_avg": None,
            "service_hours_ytd": 0,
            "chapel_attendance_pct": None,
        },
        "compliance": {
            "safety_incidents_ytd": 0,
            "audit_log_entries_30d": 0,
            "required_checks_passing": 0,
        },
    }


def build_board_dashboard_payload(*, school_id) -> dict:
    """Return board-safe aggregated metrics for the structured dashboard API.
    NOTE: Do NOT expose raw tables to board role. Aggregate and redact.
    Replace these placeholders with real Finance/Admissions/Discipline
    service calls when wiring the live data layer."""
    today = date.today()
    window_start = today - timedelta(days=90)

    return {
        "meta": {
            "school_id": str(school_id),
            "as_of": today.isoformat(),
            "window_start": window_start.isoformat(),
        },
        "finance": {
            "tuition_collection_rate": 0.0,      # 0..1
            "ar_over_30_days": 0.0,
            "aid_awarded_total": 0.0,
            "net_tuition_projected": 0.0,
        },
        "enrollment": {
            "current_enrollment": 0,
            "applications_ytd": 0,
            "acceptances_ytd": 0,
            "yield_rate": 0.0,                   # 0..1
        },
        "attendance": {
            "avg_daily_attendance": 0.0,          # 0..1
            "chronic_absenteeism_rate": 0.0,      # 0..1
        },
        "discipline": {
            "incidents_90d": 0,
            "severe_incidents_90d": 0,
        },
        "spiritual_life": {
            "chapel_participation_rate": None,    # optional
            "service_hours_ytd": None,            # optional
        },
        "crown_compass": {
            "health_score": None,                 # optional computed composite
            "notes": [],
        },
    }
