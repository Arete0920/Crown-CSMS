"""
Seed default SignalDefinition records for a school.

Usage:
    from signals.seed import seed_signals_for_school
    seed_signals_for_school(1)
"""
from .models import SignalDefinition

DEFAULTS = [
    dict(
        key="attendance_drop_30d",
        name="Attendance drop (30 days)",
        description="Flags rolling attendance below threshold.",
        severity_weight=25,
        rule={"type": "attendance_drop", "window_days": 30, "threshold_pct": 90},
    ),
    dict(
        key="gpa_drop",
        name="GPA drop",
        description="Flags GPA decline vs previous period.",
        severity_weight=20,
        rule={"type": "gpa_drop", "drop": 0.3},
    ),
    dict(
        key="tuition_delinquent",
        name="Tuition delinquent",
        description="Flags delinquency beyond threshold.",
        severity_weight=30,
        rule={"type": "tuition_delinquent", "days_past_due": 30, "amount_min": 100},
    ),
    dict(
        key="discipline_spike",
        name="Discipline spike",
        description="Flags elevated discipline incidents in a window.",
        severity_weight=15,
        rule={"type": "discipline_spike", "window_days": 30, "threshold_count": 3},
    ),
]


def seed_signals_for_school(school_id: int) -> None:
    for d in DEFAULTS:
        SignalDefinition.objects.update_or_create(
            school_id=school_id,
            key=d["key"],
            defaults={k: v for k, v in d.items() if k != "key"},
        )
