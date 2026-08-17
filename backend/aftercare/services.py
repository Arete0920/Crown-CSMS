"""Extended-care domain services using canonical UUID ownership."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from households.models import Student

from .models import (
    AftercareAttendance,
    AftercareEnrollment,
    AftercareIncident,
    AftercareMonthlyChargeRun,
    AftercarePickupContact,
    AftercareProgramConfig,
)


def to_cents(amount) -> int:
    return int(round(float(amount) * 100))


def cents_to_amount(cents: int) -> float:
    return float(cents) / 100.0


def combine_local(d: date, t: time | str) -> datetime:
    if isinstance(t, str):
        try:
            t = time.fromisoformat(t)
        except ValueError as exc:
            raise ValueError(f"Invalid configured extended-care time: {t!r}") from exc
    return timezone.make_aware(datetime.combine(d, t))


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


def _canonical_student(*, school_id, student_id) -> Student:
    student = Student.objects.filter(pk=student_id, school_id=school_id, is_active=True).first()
    if student is None:
        raise ValueError("Student is not active in this school.")
    return student


def _active_enrollment(*, school_id, student: Student, on_date: date) -> AftercareEnrollment:
    enrollment = (
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id,
            student_fk=student,
            is_active=True,
            start_date__lte=on_date,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=on_date))
        .order_by("-created_at")
        .first()
    )
    if enrollment is None:
        raise ValueError("Student is not actively enrolled in extended care.")
    dow = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][on_date.weekday()]
    if dow not in (enrollment.days_of_week or []):
        raise ValueError("Student is not scheduled for extended care on this date.")
    return enrollment


def create_ledger_charge_aftercare(school_id, student_id, amount_cents: int, description: str) -> int:
    from .integrations import create_aftercare_finance_obligation
    return create_aftercare_finance_obligation(
        school_id=school_id,
        student_id=student_id,
        amount_cents=amount_cents,
        description=description,
    )


def create_discipline_record_for_incident(school_id, student_id, description: str, severity: str):
    from .integrations import create_aftercare_discipline_incident
    return create_aftercare_discipline_incident(
        school_id=school_id,
        student_id=student_id,
        description=description,
        severity=severity,
    )


@transaction.atomic
def ensure_config(school_id) -> AftercareProgramConfig:
    cfg, _ = AftercareProgramConfig.objects.get_or_create(school_fk_id=school_id)
    return cfg


@transaction.atomic
def checkin_student(school_id, student_id, when: datetime | None = None, note: str = "") -> AftercareAttendance:
    when = when or timezone.now()
    student = _canonical_student(school_id=school_id, student_id=student_id)
    _active_enrollment(school_id=school_id, student=student, on_date=when.date())
    attendance, created = AftercareAttendance.objects.get_or_create(
        school_fk_id=school_id,
        student_fk=student,
        date=when.date(),
        defaults={"checkin_time": when, "notes": note},
    )
    if not created and note:
        attendance.notes = (attendance.notes + " | " + note).strip(" |")
        attendance.save(update_fields=["notes"])
    return attendance


@transaction.atomic
def checkout_student(
    school_id,
    student_id,
    pickup_contact_id: int | None,
    pickup_name_freeform: str,
    pickup_verified: bool,
    when: datetime | None = None,
) -> AftercareAttendance:
    when = when or timezone.now()
    student = _canonical_student(school_id=school_id, student_id=student_id)
    cfg = ensure_config(school_id)
    attendance = AftercareAttendance.objects.select_for_update().get(
        school_fk_id=school_id,
        student_fk=student,
        date=when.date(),
    )

    pickup_contact = None
    if pickup_contact_id is not None:
        pickup_contact = AftercarePickupContact.objects.filter(
            pk=pickup_contact_id,
            school_fk_id=school_id,
            student_fk=student,
            is_active=True,
        ).first()
        if pickup_contact is None:
            raise ValueError("Pickup contact is not authorized for this student and school.")

    attendance.checkout_time = when
    attendance.pickup_contact_fk = pickup_contact
    attendance.pickup_name_freeform = pickup_name_freeform or ""
    attendance.pickup_verified = bool(pickup_verified)
    fee = compute_late_fee(cfg, when.date(), when)
    attendance.late_minutes = fee.late_minutes
    attendance.late_fee_cents = fee.late_fee_cents

    if attendance.late_fee_cents > 0 and not attendance.late_fee_charge_id:
        charge_id = create_ledger_charge_aftercare(
            school_id=school_id,
            student_id=student.id,
            amount_cents=attendance.late_fee_cents,
            description=f"Aftercare Late Pickup Fee ({attendance.late_minutes} min)",
        )
        attendance.late_fee_charge_id = str(charge_id)

    attendance.save()
    return attendance


@transaction.atomic
def record_incident(
    school_id,
    student_id,
    severity: str,
    description: str,
    attendance_id: int | None = None,
    parent_notified: bool = False,
) -> AftercareIncident:
    student = _canonical_student(school_id=school_id, student_id=student_id)
    attendance = None
    if attendance_id is not None:
        attendance = AftercareAttendance.objects.filter(
            pk=attendance_id,
            school_fk_id=school_id,
            student_fk=student,
        ).first()
        if attendance is None:
            raise ValueError("Attendance record does not belong to this student and school.")

    incident = AftercareIncident.objects.create(
        school_fk_id=school_id,
        student_fk=student,
        severity=severity,
        description=description,
        attendance_fk=attendance,
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
def run_monthly_flat_billing(school_id, year: int, month: int) -> dict:
    if AftercareMonthlyChargeRun.objects.filter(school_fk_id=school_id, year=year, month=month).exists():
        return {"status": "already_ran"}

    month_start = date(year, month, 1)
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    month_end = date(next_year, next_month, 1)
    enrollments = (
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id,
            is_active=True,
            billing_model="FLAT_MONTHLY",
            start_date__lt=month_end,
            student_fk__isnull=False,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=month_start))
        .select_related("student_fk")
    )

    charged = 0
    for enrollment in enrollments:
        if not enrollment.monthly_rate:
            continue
        create_ledger_charge_aftercare(
            school_id=school_id,
            student_id=enrollment.student_fk_id,
            amount_cents=to_cents(enrollment.monthly_rate),
            description=f"Aftercare Monthly ({year}-{month:02d})",
        )
        charged += 1

    AftercareMonthlyChargeRun.objects.create(
        school_fk_id=school_id,
        year=year,
        month=month,
        notes=f"charged={charged}",
    )
    return {"status": "ok", "charged": charged}
