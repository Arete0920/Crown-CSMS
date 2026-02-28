"""
Crown Signal Engine — deterministic + explainable.
Each signal has a rule type, fires observable events, and rolls up into a
StudentRiskSnapshot. BoardExecutiveMetric is computed separately.

TODO: replace compute_student_features stubs with real module queries:
  - Attendance app
  - Gradebook app
  - Ledger / billing app
  - Discipline app
"""
from datetime import date
from django.db import transaction
from django.utils import timezone

from .models import (
    SignalDefinition,
    SignalEvent,
    StudentRiskSnapshot,
    InterventionCase,
    BoardExecutiveMetric,
)


def clamp(n: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(n)))


def risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 35:
        return "MED"
    return "LOW"


def compute_student_features(school_id: int, student_id: int) -> dict:
    """
    Gather raw features for deterministic rule evaluation.
    STUB — replace each value with a real DB query against the relevant app.
    """
    return {
        "attendance_pct_30d": 94.0,
        "gpa_current": 3.0,
        "gpa_prev": 3.2,
        "days_past_due": 0,
        "balance_due": 0.0,
        "discipline_30d": 0,
        # Aftercare signals — replace with real DB queries
        "aftercare_late_30d": 0,
        "aftercare_incident_30d": 0,
    }


def evaluate_signal(defn: SignalDefinition, features: dict) -> dict | None:
    """
    Returns a fired-event dict if the rule is triggered, otherwise None.
    Each rule type is deterministic and fully explainable via 'details'.
    """
    rule = defn.rule or {}
    rule_type = rule.get("type")

    if rule_type == "attendance_drop":
        window = int(rule.get("window_days", 30))
        threshold = float(rule.get("threshold_pct", 90))
        actual = float(features.get(f"attendance_pct_{window}d", features.get("attendance_pct_30d", 100)))
        if actual < threshold:
            return {
                "signal_key": defn.key,
                "weight": defn.severity_weight,
                "summary": f"Attendance below {threshold:.0f}% ({actual:.1f}%)",
                "details": {
                    "window_days": window,
                    "threshold_pct": threshold,
                    "attendance_pct": actual,
                },
            }

    elif rule_type == "gpa_drop":
        drop = float(rule.get("drop", 0.3))
        cur = float(features.get("gpa_current", 4.0))
        prev = float(features.get("gpa_prev", cur))
        if (prev - cur) >= drop:
            return {
                "signal_key": defn.key,
                "weight": defn.severity_weight,
                "summary": f"GPA drop {prev:.2f} → {cur:.2f}",
                "details": {
                    "gpa_prev": prev,
                    "gpa_current": cur,
                    "drop": round(prev - cur, 4),
                },
            }

    elif rule_type == "tuition_delinquent":
        days = int(rule.get("days_past_due", 30))
        min_amt = float(rule.get("amount_min", 100))
        d = int(features.get("days_past_due", 0))
        bal = float(features.get("balance_due", 0))
        if d >= days and bal >= min_amt:
            return {
                "signal_key": defn.key,
                "weight": defn.severity_weight,
                "summary": f"Tuition delinquent ({d} days, ${bal:.0f} due)",
                "details": {
                    "days_past_due": d,
                    "balance_due": bal,
                    "threshold_days": days,
                    "min_amount": min_amt,
                },
            }

    elif rule_type == "discipline_spike":
        window = int(rule.get("window_days", 30))
        threshold = int(rule.get("threshold_count", 3))
        cnt = int(features.get(f"discipline_{window}d", features.get("discipline_30d", 0)))
        if cnt >= threshold:
            return {
                "signal_key": defn.key,
                "weight": defn.severity_weight,
                "summary": f"Discipline incidents spike ({cnt} in {window} days)",
                "details": {
                    "window_days": window,
                    "count": cnt,
                    "threshold": threshold,
                },
            }

    elif rule_type == "aftercare_late_spike":
        window = int(rule.get("window_days", 30))
        threshold = int(rule.get("threshold_count", 3))
        cnt = int(features.get(f"aftercare_late_{window}d", features.get("aftercare_late_30d", 0)))
        if cnt >= threshold:
            return {
                "signal_key": defn.key,
                "weight": defn.severity_weight,
                "summary": f"Aftercare late pickups spike ({cnt} in {window} days)",
                "details": {
                    "window_days": window,
                    "count": cnt,
                    "threshold": threshold,
                },
            }

    elif rule_type == "aftercare_incident_spike":
        window = int(rule.get("window_days", 30))
        threshold = int(rule.get("threshold_count", 2))
        cnt = int(features.get(f"aftercare_incident_{window}d", features.get("aftercare_incident_30d", 0)))
        if cnt >= threshold:
            return {
                "signal_key": defn.key,
                "weight": defn.severity_weight,
                "summary": f"Aftercare incidents spike ({cnt} in {window} days)",
                "details": {
                    "window_days": window,
                    "count": cnt,
                    "threshold": threshold,
                },
            }

    return None


@transaction.atomic
def compute_snapshots_for_school(school_id: int, as_of: date | None = None):
    """
    Computes SignalEvents and StudentRiskSnapshot for all active students.
    Idempotent per (school_id, student_id, as_of_date): uses update_or_create.

    TODO: replace the demo student_ids with a real roster query, e.g.:
        from academics.models import Enrollment
        student_ids = list(
            Enrollment.objects.filter(school_id=school_id, is_active=True)
            .values_list("student_id", flat=True)
        )
    """
    as_of = as_of or timezone.now().date()

    # STUB: demo roster
    student_ids = list(range(1001, 1021))

    defs = list(
        SignalDefinition.objects.filter(school_id=school_id, is_active=True)
        .order_by("-severity_weight")
    )

    for sid in student_ids:
        features = compute_student_features(school_id, sid)

        fired = []
        score = 0
        for defn in defs:
            evt = evaluate_signal(defn, features)
            if evt:
                fired.append(evt)
                score += int(evt["weight"])

                SignalEvent.objects.create(
                    school_id=school_id,
                    student_id=sid,
                    signal_key=evt["signal_key"],
                    weight=int(evt["weight"]),
                    summary=evt["summary"],
                    details=evt["details"],
                )

        score = clamp(score)
        drivers = sorted(fired, key=lambda x: x["weight"], reverse=True)[:3]

        StudentRiskSnapshot.objects.update_or_create(
            school_id=school_id,
            student_id=sid,
            as_of_date=as_of,
            defaults={
                "risk_score": score,
                "risk_level": risk_level(score),
                "drivers": [
                    {"key": d["signal_key"], "weight": d["weight"], "summary": d["summary"]}
                    for d in drivers
                ],
            },
        )

        # Auto-open InterventionCase for HIGH-risk students
        if score >= 70:
            InterventionCase.objects.get_or_create(
                school_id=school_id,
                student_id=sid,
                status="OPEN",
                defaults={
                    "priority": "HIGH",
                    "reason": "High-risk signals triggered",
                    "linked_signals": [
                        {"key": d["signal_key"], "weight": d["weight"]}
                        for d in drivers
                    ],
                },
            )


@transaction.atomic
def compute_board_metrics(school_id: int, as_of: date | None = None):
    """
    Crown Compass 2.0 — deterministic indexes, explainable highlights/watchlist.

    TODO: replace the placeholder values with real aggregates from:
      - admissions app (enrollment_health)
      - ledger/billing app (financial_health)
      - discipline/attendance app (culture_health)
      - spiritual_life/mission metrics (mission_health)
      - StudentRiskSnapshot HIGH-count ratio (retention_risk)
    """
    as_of = as_of or timezone.now().date()

    enrollment_health = 78
    financial_health = 74
    culture_health = 81
    mission_health = 86
    retention_risk = 22

    highlights = [
        "Re-enrollment trending +2.1% YoY",
        "Attendance stable (rolling 30 days)",
    ]
    watchlist = [
        "2 family accounts >30 days past due",
    ]

    BoardExecutiveMetric.objects.update_or_create(
        school_id=school_id,
        as_of_date=as_of,
        defaults=dict(
            enrollment_health=enrollment_health,
            financial_health=financial_health,
            culture_health=culture_health,
            mission_health=mission_health,
            retention_risk=retention_risk,
            highlights=highlights,
            watchlist=watchlist,
        ),
    )
