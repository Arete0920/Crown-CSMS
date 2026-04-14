"""
Aftercare services — deterministic, explainable, no magic.

Integration points marked with CANON_* tokens:
  CANON_LEDGER_CHARGE_HOOK  — wire to your ledger create_charge call
  CANON_DISCIPLINE_HOOK     — wire to your discipline record creation
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    AftercareProgramConfig,
    AftercareEnrollment,
    AftercareAttendance,
    AftercareIncident,
    AftercareMonthlyChargeRun,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_cents(amount) -> int:
    return int(round(float(amount) * 100))


def cents_to_amount(cents: int) -> float:
    return float(cents) / 100.0


def combine_local(d: date, t: time) -> datetime:
    return timezone.make_aware(datetime.combine(d, t))


@dataclass
class LateFeeResult:
    late_minutes: int
    late_fee_cents: int


def compute_late_fee(config: AftercareProgramConfig, attendance_date: date, checkout_dt: datetime) -> LateFeeResult:
    """
    Deterministic late-fee calculation.

    Rules:
    - Any checkout after config.end_time is late.
    - First config.late_fee_grace_minutes of lateness are free.
    - Each commenced 10-minute block beyond grace costs config.late_fee_per_10_min.
    - Total fee is capped at config.late_fee_cap.
    """
    cutoff_dt = combine_local(attendance_date, config.end_time)
    delta_sec = (checkout_dt - cutoff_dt).total_seconds()
    late_minutes = max(0, int(delta_sec // 60))

    grace = int(config.late_fee_grace_minutes)
    if late_minutes <= grace:
        return LateFeeResult(late_minutes=late_minutes, late_fee_cents=0)

    billable = late_minutes - grace
    blocks = (billable + 9) // 10  # ceiling divide — 1 min = 1 block
    fee = float(config.late_fee_per_10_min) * blocks
    fee = min(fee, float(config.late_fee_cap))
    return LateFeeResult(late_minutes=late_minutes, late_fee_cents=to_cents(fee))


# ---------------------------------------------------------------------------
# Integration stubs — replace with canonical implementations
# ---------------------------------------------------------------------------

def create_ledger_charge_aftercare(school_id: int, student_id: int, amount_cents: int, description: str) -> int:
    """
    CANON_LEDGER_CHARGE_HOOK:
    Replace with your actual ledger service, e.g.:
        from ledger.services import create_charge
        from decimal import Decimal
        charge = create_charge(
            school_id=school_id, student_id=student_id,
            amount=Decimal(amount_cents) / 100, description=description
        )
        return charge.id
    """
    return 0


def create_discipline_record_for_incident(school_id: int, student_id: int, description: str, severity: str) -> int:
    """
    CANON_DISCIPLINE_HOOK:
    Replace with your discipline record creation, e.g.:
        from discipline.services import create_incident
        rec = create_incident(school_id=school_id, student_id=student_id, ...)
        return rec.id
    """
    return 0


# ---------------------------------------------------------------------------
# Core actions
# ---------------------------------------------------------------------------

@transaction.atomic
def ensure_config(school_id: int) -> AftercareProgramConfig:
    cfg, _ = AftercareProgramConfig.objects.get_or_create(school_id=school_id)
    return cfg


@transaction.atomic
def checkin_student(
    school_id: int,
    student_id: int,
    when: datetime | None = None,
    note: str = "",
) -> AftercareAttendance:
    when = when or timezone.now()
    d = when.date()

    a, created = AftercareAttendance.objects.get_or_create(
        school_id=school_id,
        student_id=student_id,
        date=d,
        defaults=dict(checkin_time=when, notes=note),
    )
    if not created and note:
        # append note without overwriting existing
        a.notes = (a.notes + " | " + note).strip(" |")
        a.save(update_fields=["notes"])
    return a


@transaction.atomic
def checkout_student(
    school_id: int,
    student_id: int,
    pickup_contact_id: int | None,
    pickup_name_freeform: str,
    pickup_verified: bool,
    when: datetime | None = None,
) -> AftercareAttendance:
    when = when or timezone.now()
    d = when.date()
    cfg = ensure_config(school_id)

    a = AftercareAttendance.objects.select_for_update().get(
        school_id=school_id, student_id=student_id, date=d
    )
    a.checkout_time = when
    a.pickup_contact_id = pickup_contact_id
    a.pickup_name_freeform = pickup_name_freeform or ""
    a.pickup_verified = bool(pickup_verified)

    fee = compute_late_fee(cfg, d, when)
    a.late_minutes = fee.late_minutes
    a.late_fee_cents = fee.late_fee_cents

    if a.late_fee_cents > 0 and not a.late_fee_charge_id:
        charge_id = create_ledger_charge_aftercare(
            school_id=school_id,
            student_id=student_id,
            amount_cents=a.late_fee_cents,
            description=f"Aftercare Late Pickup Fee ({a.late_minutes} min)",
        )
        a.late_fee_charge_id = charge_id

    a.save()
    return a


@transaction.atomic
def record_incident(
    school_id: int,
    student_id: int,
    severity: str,
    description: str,
    attendance_id: int | None = None,
    parent_notified: bool = False,
) -> AftercareIncident:
    inc = AftercareIncident.objects.create(
        school_id=school_id,
        student_id=student_id,
        severity=severity,
        description=description,
        attendance_id=attendance_id,
        parent_notified=parent_notified,
    )

    # Auto-create discipline record for MODERATE/MAJOR incidents
    if severity in ("MODERATE", "MAJOR"):
        inc.discipline_record_id = create_discipline_record_for_incident(
            school_id=school_id,
            student_id=student_id,
            description=f"Aftercare incident ({severity}): {description}",
            severity=severity,
        )
        inc.save(update_fields=["discipline_record_id"])

    return inc


@transaction.atomic
def run_monthly_flat_billing(school_id: int, year: int, month: int) -> dict:
    """
    Charges families/students enrolled under FLAT_MONTHLY.
    Idempotent: AftercareMonthlyChargeRun prevents double-runs.
    """
    if AftercareMonthlyChargeRun.objects.filter(school_id=school_id, year=year, month=month).exists():
        return {"status": "already_ran"}

    month_start = date(year, month, 1)
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    month_end = date(next_year, next_month, 1)

    enrollments = AftercareEnrollment.objects.filter(
        school_id=school_id,
        is_active=True,
        billing_model="FLAT_MONTHLY",
        start_date__lt=month_end,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=month_start)
    )

    charged = 0
    for e in enrollments:
        if not e.monthly_rate:
            continue
        create_ledger_charge_aftercare(
            school_id=school_id,
            student_id=e.student_id,
            amount_cents=to_cents(e.monthly_rate),
            description=f"Aftercare Monthly ({year}-{month:02d})",
        )
        charged += 1

    AftercareMonthlyChargeRun.objects.create(
        school_id=school_id, year=year, month=month, notes=f"charged={charged}"
    )
    return {"status": "ok", "charged": charged}


