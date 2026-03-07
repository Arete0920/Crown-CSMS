"""
Crown Signal Engine v2 -- deterministic + explainable.

Migrated to UUID FKs (2026-03-02):
  SignalDefinition, StudentRiskSnapshot, SignalEvent, InterventionCase, and
  BoardExecutiveMetric all have proper ForeignKey references to core.School
  (UUID PK) and households.Student (UUID PK).

  Aftercare queries now use the new school_fk / student_fk nullable FK fields
  added via aftercare.migrations.0002_add_uuid_fks.  Records seeded by
  seed_demo have these FKs set; old integer-only rows are invisible to the
  engine until back-filled.

Public callables:
  compute_snapshots_for_school(school)       -- nightly / on-demand
  compute_board_metrics(school)              -- board dashboard roll-up
"""
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    BoardExecutiveMetric,
    InterventionCase,
    SignalDefinition,
    SignalEvent,
    StudentRiskSnapshot,
)


# ------------------------------------------------------------------ helpers --


def clamp(n: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(n)))


def risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 35:
        return "MED"
    return "LOW"


def _window_start(days: int) -> date:
    return timezone.now().date() - timedelta(days=days)


# ---------------------------------------------- feature extraction per student


def compute_student_features(school, student) -> dict:
    """
    Gather raw features for deterministic rule evaluation.

    school  -- core.School instance
    student -- households.Student instance

    Aftercare features are wired to real DB queries via the new UUID FK columns
    (school_fk / student_fk on aftercare models).

    GPA, discipline, and finance signals remain at safe zero values until those
    apps expose queryable views that join through UUID FKs -- no integer casting.
    """
    from aftercare.models import AftercareAttendance, AftercareIncident

    window_30 = _window_start(30)

    aftercare_late_30d = AftercareAttendance.objects.filter(
        school_fk=school,
        student_fk=student,
        date__gte=window_30,
        late_minutes__gt=0,
    ).count()

    aftercare_incident_30d = AftercareIncident.objects.filter(
        school_fk=school,
        student_fk=student,
        occurred_at__date__gte=window_30,
    ).count()

    return {
        "attendance_pct_30d": 100.0,       # not wired: UUID join to academics TBD
        "gpa_current": 4.0,                # not wired: UUID join to gradebook TBD
        "gpa_prev": 4.0,                   # not wired
        "days_past_due": 0,                # not wired: UUID join to finance TBD
        "balance_due": 0.0,                # not wired
        "discipline_30d": 0,               # not wired: UUID join to discipline TBD
        "aftercare_late_30d": aftercare_late_30d,
        "aftercare_incident_30d": aftercare_incident_30d,
    }


# -------------------------------------------------- deterministic rule engine


def evaluate_signal(defn: SignalDefinition, features: dict) -> dict | None:
    """
    Returns a fired-event dict if the rule is triggered, otherwise None.
    Each rule type is deterministic and fully explainable.
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
                "summary": f"GPA drop {prev:.2f} -> {cur:.2f}",
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
                "summary": f"Aftercare late pickups ({cnt} in {window} days)",
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
                "summary": f"Aftercare incidents ({cnt} in {window} days)",
                "details": {
                    "window_days": window,
                    "count": cnt,
                    "threshold": threshold,
                },
            }

    return None


# --------------------------------------------------- school-level batch compute


@transaction.atomic
def compute_snapshots_for_school(school, as_of: date | None = None):
    """
    Compute SignalEvents and StudentRiskSnapshot for all active aftercare students.
    Idempotent per (school, student, as_of_date): uses update_or_create.

    school -- core.School instance
    """
    as_of = as_of or timezone.now().date()

    from aftercare.models import AftercareEnrollment

    # Roster: active aftercare enrollments with UUID FK populated.
    enrollments = (
        AftercareEnrollment.objects.filter(school_fk=school, is_active=True)
        .exclude(student_fk__isnull=True)
        .select_related("student_fk")
        .distinct()
    )

    students = list({e.student_fk for e in enrollments})

    if not students:
        return

    defs = list(
        SignalDefinition.objects.filter(school=school, is_active=True)
        .order_by("-severity_weight")
    )

    for student in students:
        features = compute_student_features(school, student)

        fired = []
        score = 0
        for defn in defs:
            evt = evaluate_signal(defn, features)
            if evt:
                fired.append(evt)
                score += int(evt["weight"])

                SignalEvent.objects.create(
                    school=school,
                    student=student,
                    signal_key=evt["signal_key"],
                    weight=int(evt["weight"]),
                    summary=evt["summary"],
                    details=evt["details"],
                )

        score = clamp(score)
        drivers = sorted(fired, key=lambda x: x["weight"], reverse=True)[:3]

        StudentRiskSnapshot.objects.update_or_create(
            school=school,
            student=student,
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

        if score >= 70:
            InterventionCase.objects.get_or_create(
                school=school,
                student=student,
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
def compute_board_metrics(school, as_of: date | None = None):
    """
    Crown Compass 2.0 -- deterministic indexes, explainable highlights/watchlist.

    Wired:
      retention_risk   -- % of aftercare students with HIGH risk snapshot
      aftercare watchlist -- late pickup count (30d)

    UUID-blocked (safe defaults until those apps surface UUID-queryable views):
      enrollment_health, financial_health, culture_health, mission_health

    school -- core.School instance
    """
    as_of = as_of or timezone.now().date()

    from aftercare.models import AftercareAttendance, AftercareEnrollment

    # Active aftercare students (UUID FK routed)
    enrollments = (
        AftercareEnrollment.objects.filter(school_fk=school, is_active=True)
        .exclude(student_fk__isnull=True)
        .select_related("student_fk")
        .distinct()
    )
    students = list({e.student_fk for e in enrollments})
    total_active = len(students)

    if total_active > 0:
        high_risk_count = (
            StudentRiskSnapshot.objects.filter(
                school=school,
                student__in=students,
                risk_level="HIGH",
            )
            .values("student")
            .distinct()
            .count()
        )
        retention_risk = clamp(round(high_risk_count / total_active * 100))
    else:
        retention_risk = 0

    window_30 = _window_start(30)
    total_late = AftercareAttendance.objects.filter(
        school_fk=school,
        date__gte=window_30,
        late_minutes__gt=0,
    ).count()

    highlights = []
    watchlist = []

    if total_active > 0:
        highlights.append(f"{total_active} student(s) actively enrolled in aftercare")
    if total_late > 0:
        watchlist.append(f"{total_late} late pickup(s) in the last 30 days")
    if retention_risk >= 20:
        watchlist.append(f"{retention_risk}% of aftercare students currently flagged HIGH risk")

    # UUID-blocked indexes -- safe defaults
    enrollment_health = 0
    financial_health = 0
    culture_health = 0
    mission_health = 0

    BoardExecutiveMetric.objects.update_or_create(
        school=school,
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
