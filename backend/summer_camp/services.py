from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone

from .models import (
    SummerCampAttendance,
    SummerCampBillingLedgerLink,
    SummerCampEnrollment,
    SummerCampFormRequirement,
    SummerCampHealthReview,
    SummerCampIncident,
    SummerCampPickupContact,
    SummerCampProgram,
    SummerCampProgramConfig,
    SummerCampSession,
    SummerCampStaffAssignment,
)


@dataclass
class CapacityState:
    registered_count: int
    waitlisted_count: int
    has_open_capacity: bool


def ensure_config(school_id):
    config, _ = SummerCampProgramConfig.objects.get_or_create(school_id=school_id)
    return config


@transaction.atomic
def create_program(school_id, payload: dict):
    return SummerCampProgram.objects.create(school_id=school_id, **payload)


@transaction.atomic
def update_program(school_id, program_id, payload: dict):
    program = SummerCampProgram.objects.get(id=program_id, school_id=school_id)
    for key, value in payload.items():
        setattr(program, key, value)
    program.save()
    return program


@transaction.atomic
def create_session(school_id, payload: dict):
    return SummerCampSession.objects.create(school_id=school_id, **payload)


@transaction.atomic
def update_session(school_id, session_id, payload: dict):
    session = SummerCampSession.objects.get(id=session_id, school_id=school_id)
    for key, value in payload.items():
        setattr(session, key, value)
    session.save()
    return session


def compute_session_capacity(school_id, session_id) -> CapacityState:
    session = SummerCampSession.objects.get(id=session_id, school_id=school_id)
    counts = (
        SummerCampEnrollment.objects.filter(school_id=school_id, session_id=session_id)
        .values("status")
        .annotate(total=Count("id"))
    )
    registered_count = next((row["total"] for row in counts if row["status"] == "REGISTERED"), 0)
    waitlisted_count = next((row["total"] for row in counts if row["status"] == "WAITLISTED"), 0)
    return CapacityState(
        registered_count=registered_count,
        waitlisted_count=waitlisted_count,
        has_open_capacity=registered_count < session.capacity,
    )


def _next_waitlist_position(school_id, session_id):
    current_max = (
        SummerCampEnrollment.objects.filter(
            school_id=school_id,
            session_id=session_id,
            status="WAITLISTED",
        ).aggregate(max_pos=Max("waitlist_position"))["max_pos"]
        or 0
    )
    return int(current_max) + 1


@transaction.atomic
def enroll_camper(school_id, student_id, session_id, payload: dict):
    state = compute_session_capacity(school_id, session_id)
    status = "REGISTERED" if state.has_open_capacity else "WAITLISTED"
    waitlist_position = None if status == "REGISTERED" else _next_waitlist_position(school_id, session_id)

    enrollment = SummerCampEnrollment.objects.create(
        school_id=school_id,
        student_id=student_id,
        session_id=session_id,
        status=status,
        waitlist_position=waitlist_position,
        **payload,
    )
    compute_camper_readiness(school_id, enrollment.id)
    return enrollment


@transaction.atomic
def cancel_enrollment(school_id, enrollment_id, reason=""):
    enrollment = SummerCampEnrollment.objects.select_for_update().get(id=enrollment_id, school_id=school_id)
    enrollment.status = "CANCELLED"
    blockers = ["CANCELLED"]
    if reason:
        blockers.append(f"REASON:{reason}")
    enrollment.readiness_status = "BLOCKED"
    enrollment.readiness_blockers = blockers
    enrollment.save(update_fields=["status", "readiness_status", "readiness_blockers"])
    move_waitlist_if_capacity_available(school_id, enrollment.session_id)
    return enrollment


@transaction.atomic
def move_waitlist_if_capacity_available(school_id, session_id):
    state = compute_session_capacity(school_id, session_id)
    if not state.has_open_capacity:
        return None

    next_waitlisted = (
        SummerCampEnrollment.objects.select_for_update()
        .filter(school_id=school_id, session_id=session_id, status="WAITLISTED")
        .order_by("waitlist_position", "created_at")
        .first()
    )
    if not next_waitlisted:
        return None

    next_waitlisted.status = "REGISTERED"
    next_waitlisted.waitlist_position = None
    next_waitlisted.save(update_fields=["status", "waitlist_position"])
    compute_camper_readiness(school_id, next_waitlisted.id)
    return next_waitlisted


@transaction.atomic
def create_form_requirement(school_id, session_id, payload: dict):
    requirement, _ = SummerCampFormRequirement.objects.update_or_create(
        school_id=school_id,
        session_id=session_id,
        form_type=payload["form_type"],
        defaults=payload,
    )
    return requirement


def compute_form_status(school_id, enrollment_id):
    enrollment = SummerCampEnrollment.objects.get(id=enrollment_id, school_id=school_id)
    required_count = SummerCampFormRequirement.objects.filter(
        school_id=school_id,
        session_id=enrollment.session_id,
        required=True,
    ).count()
    if required_count == 0:
        return "COMPLETE"
    return enrollment.form_status


@transaction.atomic
def create_health_review(school_id, enrollment_id, payload: dict):
    review, _ = SummerCampHealthReview.objects.update_or_create(
        school_id=school_id,
        enrollment_id=enrollment_id,
        defaults=payload,
    )
    compute_camper_readiness(school_id, enrollment_id)
    return review


@transaction.atomic
def mark_health_review_complete(school_id, enrollment_id, reviewer_id):
    review = SummerCampHealthReview.objects.get(school_id=school_id, enrollment_id=enrollment_id)
    review.review_status = "APPROVED"
    review.reviewed_by_id = reviewer_id
    review.reviewed_at = timezone.now()
    review.save(update_fields=["review_status", "reviewed_by", "reviewed_at"])
    enrollment = review.enrollment
    enrollment.health_status = "APPROVED"
    enrollment.save(update_fields=["health_status"])
    compute_camper_readiness(school_id, enrollment_id)
    return review


@transaction.atomic
def checkin_camper(school_id, student_id, session_id, when=None, note=""):
    when = when or timezone.now()
    attendance, _ = SummerCampAttendance.objects.get_or_create(
        school_id=school_id,
        student_id=student_id,
        session_id=session_id,
        date=when.date(),
        defaults={"checkin_time": when, "notes": note},
    )
    return attendance


@transaction.atomic
def checkout_camper(
    school_id,
    student_id,
    session_id,
    pickup_contact_id=None,
    pickup_verified=False,
    when=None,
):
    when = when or timezone.now()
    attendance = SummerCampAttendance.objects.get(
        school_id=school_id,
        student_id=student_id,
        session_id=session_id,
        date=when.date(),
    )
    attendance.checkout_time = when
    attendance.pickup_contact_id = pickup_contact_id
    attendance.pickup_verified = bool(pickup_verified)
    attendance.save(update_fields=["checkout_time", "pickup_contact", "pickup_verified"])
    return attendance


@transaction.atomic
def assign_staff(school_id, session_id, staff_user_id, role, assigned_date=None):
    assignment, _ = SummerCampStaffAssignment.objects.get_or_create(
        school_id=school_id,
        session_id=session_id,
        staff_user_id=staff_user_id,
        role=role,
        defaults={"assigned_date": assigned_date or timezone.now().date()},
    )
    return assignment


def compute_staff_ratio_status(school_id, session_id):
    session = SummerCampSession.objects.get(id=session_id, school_id=school_id)
    config = ensure_config(school_id)
    registered = SummerCampEnrollment.objects.filter(
        school_id=school_id,
        session_id=session_id,
        status="REGISTERED",
    ).count()
    required_staff = (registered + max(config.default_staff_ratio - 1, 0)) // max(config.default_staff_ratio, 1)
    assigned_staff = SummerCampStaffAssignment.objects.filter(school_id=school_id, session_id=session_id).count()
    return {
        "session_id": str(session.id),
        "registered": registered,
        "required_staff": required_staff,
        "assigned_staff": assigned_staff,
        "coverage_status": "OK" if assigned_staff >= required_staff else "GAP",
    }


@transaction.atomic
def create_ledger_charge_summer_camp(school_id, enrollment_id, amount_cents, charge_type="SESSION", charge_id=""):
    return SummerCampBillingLedgerLink.objects.create(
        school_id=school_id,
        enrollment_id=enrollment_id,
        amount_cents=amount_cents,
        charge_type=charge_type,
        charge_id=charge_id,
        status="OPEN",
    )


@transaction.atomic
def record_incident(
    school_id,
    student_id,
    session_id,
    severity,
    description,
    attendance_id=None,
    parent_notified=False,
    health_followup_required=False,
    category="",
):
    incident = SummerCampIncident.objects.create(
        school_id=school_id,
        student_id=student_id,
        session_id=session_id,
        severity=severity,
        category=category,
        description=description,
        parent_notified=parent_notified,
        health_followup_required=health_followup_required,
    )
    return incident


@transaction.atomic
def compute_camper_readiness(school_id, enrollment_id):
    enrollment = SummerCampEnrollment.objects.get(id=enrollment_id, school_id=school_id)
    blockers = []

    if enrollment.status == "WAITLISTED":
        blockers.append("WAITLISTED")

    if enrollment.balance_due_cents > 0 and enrollment.payment_required_before_attendance:
        blockers.append("MISSING_PAYMENT")

    if compute_form_status(school_id, enrollment_id) != "COMPLETE":
        blockers.append("MISSING_FORMS")

    if enrollment.health_status == "NEEDS_REVIEW":
        blockers.append("HEALTH_REVIEW_REQUIRED")

    has_pickup_contact = SummerCampPickupContact.objects.filter(
        school_id=school_id,
        enrollment_id=enrollment_id,
        is_active=True,
    ).exists()
    if not has_pickup_contact:
        blockers.append("PICKUP_CONTACT_MISSING")

    ratio = compute_staff_ratio_status(school_id, enrollment.session_id)
    if ratio["coverage_status"] != "OK":
        blockers.append("STAFF_REVIEW_REQUIRED")

    if blockers:
        enrollment.readiness_status = "BLOCKED"
    else:
        enrollment.readiness_status = "READY"

    enrollment.readiness_blockers = blockers
    enrollment.save(update_fields=["readiness_status", "readiness_blockers"])
    return {
        "status": enrollment.readiness_status,
        "blockers": blockers,
    }


def board_summary(school_id):
    today = timezone.now().date()
    session_count = SummerCampSession.objects.filter(school_id=school_id).count()
    registered = SummerCampEnrollment.objects.filter(school_id=school_id, status="REGISTERED").count()
    waitlisted = SummerCampEnrollment.objects.filter(school_id=school_id, status="WAITLISTED").count()
    missing_forms = SummerCampEnrollment.objects.filter(school_id=school_id, form_status__in=["MISSING", "IN_PROGRESS", "NOT_STARTED"]).count()
    health_reviews_needed = SummerCampEnrollment.objects.filter(school_id=school_id, health_status="NEEDS_REVIEW").count()
    outstanding_balances = SummerCampEnrollment.objects.filter(
        school_id=school_id,
        payment_status__in=["DEPOSIT_DUE", "BALANCE_DUE", "PAST_DUE"],
    ).count()
    incidents_mtd = SummerCampIncident.objects.filter(
        school_id=school_id,
        created_at__date__year=today.year,
        created_at__date__month=today.month,
    ).count()
    gross_revenue_cents = (
        SummerCampBillingLedgerLink.objects.filter(school_id=school_id)
        .exclude(status="CANCELLED")
        .aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )

    return {
        "as_of": str(today),
        "sessions": session_count,
        "registered_campers": registered,
        "waitlist_count": waitlisted,
        "missing_forms": missing_forms,
        "health_review_count": health_reviews_needed,
        "outstanding_balances": outstanding_balances,
        "incidents_mtd": incidents_mtd,
        "gross_revenue_cents": gross_revenue_cents,
    }


def missing_forms(school_id):
    qs = SummerCampEnrollment.objects.filter(
        school_id=school_id,
        form_status__in=["NOT_STARTED", "MISSING", "IN_PROGRESS"],
    ).select_related("session", "student")
    return [
        {
            "enrollment_id": str(e.id),
            "session_id": str(e.session_id),
            "session_name": e.session.name,
            "student_id": str(e.student_id) if e.student_id else None,
            "form_status": e.form_status,
            "readiness_status": e.readiness_status,
        }
        for e in qs
    ]


def health_review_queue(school_id):
    qs = SummerCampEnrollment.objects.filter(school_id=school_id, health_status="NEEDS_REVIEW").select_related("session", "student")
    return [
        {
            "enrollment_id": str(e.id),
            "session_id": str(e.session_id),
            "session_name": e.session.name,
            "student_id": str(e.student_id) if e.student_id else None,
            "health_status": e.health_status,
            "readiness_status": e.readiness_status,
        }
        for e in qs
    ]


def parent_student_summary(school_id, student_id):
    enrollments = SummerCampEnrollment.objects.filter(school_id=school_id, student_id=student_id).select_related("session")
    return [
        {
            "enrollment_id": str(e.id),
            "session_id": str(e.session_id),
            "session_name": e.session.name,
            "status": e.status,
            "form_status": e.form_status,
            "payment_status": e.payment_status,
            "health_status": e.health_status,
            "pickup_status": e.pickup_status,
            "readiness_status": e.readiness_status,
            "waitlist_position": e.waitlist_position,
            "balance_due_cents": e.balance_due_cents,
        }
        for e in enrollments
    ]


def roster_today(school_id):
    today = timezone.now().date()
    enrollments = SummerCampEnrollment.objects.filter(
        school_id=school_id,
        status="REGISTERED",
        session__start_date__lte=today,
        session__end_date__gte=today,
    ).select_related("session", "student")
    attendance = {
        (a.session_id, a.student_id): a
        for a in SummerCampAttendance.objects.filter(school_id=school_id, date=today)
    }
    rows = []
    for e in enrollments:
        key = (e.session_id, e.student_id)
        a = attendance.get(key)
        rows.append(
            {
                "enrollment_id": str(e.id),
                "session_id": str(e.session_id),
                "session_name": e.session.name,
                "student_id": str(e.student_id) if e.student_id else None,
                "student_name": (
                    f"{e.student.first_name} {e.student.last_name}" if e.student else "External Camper"
                ),
                "readiness_status": e.readiness_status,
                "readiness_blockers": e.readiness_blockers,
                "checkin_time": a.checkin_time.isoformat() if a else None,
                "checkout_time": a.checkout_time.isoformat() if a and a.checkout_time else None,
                "pickup_verified": bool(a.pickup_verified) if a else False,
                "form_status": e.form_status,
                "health_status": e.health_status,
                "payment_status": e.payment_status,
                "pickup_status": e.pickup_status,
            }
        )
    return {
        "date": str(today),
        "rows": rows,
    }
