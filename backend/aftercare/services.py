"""Extended-care domain services using canonical UUID ownership."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def care_timezone(school_id):
    """Resolve a tenant's IANA timezone; invalid configuration fails closed."""
    from core.models import School

    name = School.objects.filter(pk=school_id, is_active=True).values_list("timezone", flat=True).first()
    if not name:
        raise ValueError("An active school with a configured timezone is required for extended care.")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, TypeError, ValueError) as exc:
        raise ValueError("A valid school timezone is required for extended care.") from exc


def school_local_date(school_id, stamp: datetime) -> date:
    """Daily custody records belong to the school's civil day, not the UTC day."""
    if timezone.is_naive(stamp):
        raise ValueError("Extended-care timestamps must contain timezone information.")
    return stamp.astimezone(care_timezone(school_id)).date()


def combine_local(d: date, t: time | str, tz=None) -> datetime:
    if isinstance(t, str):
        try:
            t = time.fromisoformat(t)
        except ValueError as exc:
            raise ValueError(f"Invalid configured extended-care time: {t!r}") from exc
    return timezone.make_aware(datetime.combine(d, t), timezone=tz or timezone.get_default_timezone())


@dataclass
class LateFeeResult:
    late_minutes: int
    late_fee_cents: int


def compute_late_fee(config: AftercareProgramConfig, attendance_date: date, checkout_dt: datetime) -> LateFeeResult:
    # Legacy integer-only config tests use the Django timezone; canonical
    # school configurations always use their explicit local operating timezone.
    configured_tz = care_timezone(config.school_fk_id) if config.school_fk_id else timezone.get_default_timezone()
    cutoff_dt = combine_local(attendance_date, config.end_time, tz=configured_tz)
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


def _active_enrollment(*, school_id, student: Student, on_date: date, care_session: str = "PM") -> AftercareEnrollment:
    enrollment = (
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id,
            student_fk=student,
            care_session=care_session,
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
def checkin_student(school_id, student_id, when: datetime | None = None, note: str = "", care_session: str = "PM") -> AftercareAttendance:
    if care_session not in ("AM", "PM"):
        raise ValueError("Invalid care session.")
    when = when or timezone.now()
    attendance_day = school_local_date(school_id, when)
    student = _canonical_student(school_id=school_id, student_id=student_id)
    _active_enrollment(school_id=school_id, student=student, on_date=attendance_day, care_session=care_session)
    attendance, created = AftercareAttendance.objects.select_for_update().get_or_create(
        school_fk_id=school_id,
        student_fk=student,
        date=attendance_day,
        care_session=care_session,
        defaults={"checkin_time": when, "notes": note},
    )
    if not created and attendance.checkout_time is not None:
        raise ValueError("Extended-care session has already been closed.")
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
    care_session: str = "PM",
) -> AftercareAttendance:
    if care_session != "PM":
        raise ValueError("Morning care requires a verified school handoff, not pickup checkout.")
    # Check the two release prerequisites before any attendance or finance write.
    # The staff assertion does not replace an active school/student pickup grant.
    if pickup_verified is not True:
        raise ValueError("Pickup identity must be verified before checkout.")
    if pickup_contact_id is None:
        raise ValueError("An active authorized pickup contact is required before checkout.")

    when = when or timezone.now()
    attendance_day = school_local_date(school_id, when)
    student = _canonical_student(school_id=school_id, student_id=student_id)
    attendance = AftercareAttendance.objects.select_for_update().get(
        school_fk_id=school_id,
        student_fk=student,
        date=attendance_day,
        care_session="PM",
    )
    if attendance.checkout_time is not None:
        raise ValueError("Student has already been checked out.")
    if when < attendance.checkin_time:
        raise ValueError("Checkout cannot precede check-in.")

    pickup_contact = AftercarePickupContact.objects.filter(
        pk=pickup_contact_id,
        school_fk_id=school_id,
        student_fk=student,
        is_active=True,
    ).first()
    if pickup_contact is None:
        raise ValueError("Pickup contact is not authorized for this student and school.")

    cfg = ensure_config(school_id)
    attendance.checkout_time = when
    attendance.pickup_contact_fk = pickup_contact
    # Record the canonical authorized contact; never trust a freeform name.
    attendance.pickup_name_freeform = pickup_contact.name
    attendance.pickup_verified = True
    fee = compute_late_fee(cfg, attendance_day, when)
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
def handoff_student_to_school(school_id, student_id, receiving_user, when: datetime | None = None) -> AftercareAttendance:
    """Close a morning session only when a current-school staff recipient attests receipt."""
    from core.models import School, Staff
    from core.permissions import user_has_permission

    when = when or timezone.now()
    attendance_day = school_local_date(school_id, when)
    if not getattr(receiving_user, "is_authenticated", False) or not getattr(receiving_user, "is_active", False):
        raise ValueError("An active receiving staff member is required.")
    if getattr(receiving_user, "school_id", None) != school_id:
        raise ValueError("Receiving staff member must belong to this school.")
    staff_id = getattr(receiving_user, "staff_id", None)
    if not staff_id or not Staff.objects.filter(
        pk=staff_id, school_id=school_id, status="ACTIVE",
    ).exists():
        raise ValueError("An active school staff assignment is required for handoff.")
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None or not user_has_permission(receiving_user, "extended_care.edit", school=school):
        raise ValueError("Receiving staff member lacks school-scoped handoff authority.")
    student = _canonical_student(school_id=school_id, student_id=student_id)
    attendance = AftercareAttendance.objects.select_for_update().filter(
        school_fk_id=school_id, student_fk=student, date=attendance_day, care_session="AM",
    ).first()
    if attendance is None:
        raise ValueError("Morning check-in is required before handoff.")
    if attendance.handoff_time is not None or attendance.checkout_time is not None:
        raise ValueError("Morning handoff has already been recorded.")
    if when < attendance.checkin_time:
        raise ValueError("Handoff cannot precede check-in.")
    attendance.handoff_time = when
    attendance.handoff_recipient = receiving_user
    attendance.handoff_verified = True
    attendance.checkout_time = when
    attendance.save(update_fields=["handoff_time", "handoff_recipient", "handoff_verified", "checkout_time"])
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
            description=f"Extended Care {enrollment.care_session} Monthly ({year}-{month:02d})",
        )
        charged += 1

    AftercareMonthlyChargeRun.objects.create(
        school_fk_id=school_id,
        year=year,
        month=month,
        notes=f"charged={charged}",
    )
    return {"status": "ok", "charged": charged}
