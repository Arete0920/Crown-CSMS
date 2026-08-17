from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    AftercareAttendance,
    AftercareEnrollment,
    AftercareIncident,
    AftercareMonthlyChargeRun,
    AftercareProgramConfig,
)


def to_cents(amount) -> int:
    return int(round(float(amount) * 100))


def cents_to_amount(cents: int) -> float:
    return float(cents) / 100.0


def combine_local(d: date, t: time) -> datetime:
    value = datetime.combine(d, t)
    return timezone.make_aware(value, timezone.get_current_timezone())


@dataclass
class LateFeeResult:
    late_minutes: int
    late_fee_cents: int


def compute_late_fee(config: AftercareProgramConfig, attendance_date: date, checkout_dt: datetime) -> LateFeeResult:
    cutoff_dt = combine_local(attendance_date, config.end_time)
    delta_sec = (checkout_dt - cutoff_dt).total_seconds()
    late_minutes = max(0, int(delta_sec // 60))
    grace = int(config.late_fee_grace_minutes)
    if late_minutes <= grace:
        return LateFeeResult(late_minutes=late_minutes, late_fee_cents=0)
    billable = late_minutes - grace
    blocks = (billable + 9) // 10
    fee = min(float(config.late_fee_per_10_min) * blocks, float(config.late_fee_cap))
    return LateFeeResult(late_minutes=late_minutes, late_fee_cents=to_cents(fee))


def _student_for_school(school_id, student_id):
    from households.models import Student

    try:
        return Student.objects.get(pk=student_id, school_id=school_id, is_active=True)
    except Student.DoesNotExist as exc:
        raise ValidationError("Aftercare student is not active in the requested school.") from exc


def create_ledger_charge_aftercare(*, school_id, student_id, amount_cents: int, description: str, reference: str) -> int:
    from .integrations import create_aftercare_finance_obligation

    return create_aftercare_finance_obligation(
        school_id=school_id,
        student_id=student_id,
        amount_cents=amount_cents,
        description=description,
        reference=reference,
    )


def create_discipline_record_for_incident(*, school_id, student_id, description: str, severity: str):
    from .integrations import create_aftercare_discipline_incident

    return create_aftercare_discipline_incident(
        school_id=school_id,
        student_id=student_id,
        description=description,
        severity=severity,
    )


@transaction.atomic
def ensure_config(school_id) -> AftercareProgramConfig:
    cfg, _ = AftercareProgramConfig.objects.get_or_create(
        school_fk_id=school_id,
        defaults={"school_id": None},
    )
    return cfg


@transaction.atomic
def checkin_student(*, school_id, student_id, when: datetime | None = None, note: str = "") -> AftercareAttendance:
    student = _student_for_school(school_id, student_id)
    when = when or timezone.now()
    attendance, created = AftercareAttendance.objects.get_or_create(
        school_fk_id=school_id,
        student_fk=student,
        date=when.date(),
        defaults={
            "school_id": None,
            "student_id": None,
            "checkin_time": when,
            "notes": note,
        },
    )
    if not created and note:
        attendance.notes = (attendance.notes + " | " + note).strip(" |")
        attendance.save(update_fields=["notes"])
    return attendance


@transaction.atomic
def checkout_student(
    *,
    school_id,
    student_id,
    pickup_contact_id: int | None,
    pickup_name_freeform: str,
    pickup_verified: bool,
    when: datetime | None = None,
) -> AftercareAttendance:
    _student_for_school(school_id, student_id)
    when = when or timezone.now()
    attendance = AftercareAttendance.objects.select_for_update().get(
        school_fk_id=school_id,
        student_fk_id=student_id,
        date=when.date(),
    )
    cfg = ensure_config(school_id)
    attendance.checkout_time = when
    attendance.pickup_contact_id = pickup_contact_id
    attendance.pickup_name_freeform = pickup_name_freeform or ""
    attendance.pickup_verified = bool(pickup_verified)

    fee = compute_late_fee(cfg, attendance.date, when)
    attendance.late_minutes = fee.late_minutes
    attendance.late_fee_cents = fee.late_fee_cents
    if attendance.late_fee_cents > 0 and not attendance.late_fee_charge_id:
        attendance.late_fee_charge_id = create_ledger_charge_aftercare(
            school_id=school_id,
            student_id=student_id,
            amount_cents=attendance.late_fee_cents,
            description=f"Aftercare Late Pickup Fee ({attendance.late_minutes} min)",
            reference=f"aftercare-late:{attendance.id}",
        )
    attendance.save()
    return attendance


@transaction.atomic
def record_incident(
    *,
    school_id,
    student_id,
    severity: str,
    description: str,
    attendance_id: int | None = None,
    parent_notified: bool = False,
) -> AftercareIncident:
    student = _student_for_school(school_id, student_id)
    if attendance_id is not None and not AftercareAttendance.objects.filter(
        pk=attendance_id,
        school_fk_id=school_id,
        student_fk=student,
    ).exists():
        raise ValidationError("Aftercare attendance does not match the student and school.")

    incident = AftercareIncident.objects.create(
        school_fk_id=school_id,
        student_fk=student,
        school_id=None,
        student_id=None,
        severity=severity,
        description=description,
        attendance_id=attendance_id,
        parent_notified=parent_notified,
    )
    if severity in ("MODERATE", "MAJOR"):
        incident.discipline_record_id = create_discipline_record_for_incident(
            school_id=school_id,
            student_id=student.id,
            description=f"Aftercare incident ({severity}): {description}",
            severity=severity,
        )
        incident.save(update_fields=["discipline_record_id"])
    return incident


@transaction.atomic
def run_monthly_flat_billing(*, school_id, year: int, month: int) -> dict:
    if AftercareMonthlyChargeRun.objects.filter(school_fk_id=school_id, year=year, month=month).exists():
        return {"status": "already_ran"}

    month_start = date(year, month, 1)
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    month_end = date(next_year, next_month, 1)
    enrollments = AftercareEnrollment.objects.filter(
        school_fk_id=school_id,
        student_fk__isnull=False,
        is_active=True,
        billing_model="FLAT_MONTHLY",
        start_date__lt=month_end,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=month_start))

    charged = 0
    for enrollment in enrollments:
        if not enrollment.monthly_rate:
            continue
        create_ledger_charge_aftercare(
            school_id=school_id,
            student_id=enrollment.student_fk_id,
            amount_cents=to_cents(enrollment.monthly_rate),
            description=f"Aftercare Monthly ({year}-{month:02d})",
            reference=f"aftercare-month:{year:04d}{month:02d}:{enrollment.id}",
        )
        charged += 1

    AftercareMonthlyChargeRun.objects.create(
        school_fk_id=school_id,
        school_id=None,
        year=year,
        month=month,
        notes=f"charged={charged}",
    )
    return {"status": "ok", "charged": charged}
