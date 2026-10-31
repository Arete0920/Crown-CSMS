from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone

from households.models import Student

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
    """Register only a verified same-school child; serialize seat allocation per session."""
    session = SummerCampSession.objects.select_for_update().filter(
        pk=session_id, school_id=school_id, status="PUBLISHED",
    ).first()
    if session is None:
        raise ValueError("Camp session is unavailable for registration.")

    # External/standalone children require a real provisioned camper identity.
    # Do not create a nullable-student registration that cannot be supervised.
    student = Student.objects.select_related("household").filter(
        pk=student_id, school_id=school_id, is_active=True,
    ).first() if student_id else None
    if student is None or student.household.school_id != school_id:
        raise ValueError("Camper is not an active member of the requested school.")

    incoming = dict(payload)
    if incoming.get("household_id") is not None and str(incoming["household_id"]) != str(student.household_id):
        raise ValueError("Registration household does not match the camper.")
    # Registration is not clearance: never accept client-supplied paid,
    # health-approved, form-complete or fee-waived assertions as evidence.
    price_cents = int(getattr(session, "price_cents", 0) or 0)
    deposit_cents = int(getattr(session, "deposit_cents", 0) or 0)
    if price_cents < 0 or deposit_cents < 0:
        raise ValueError("Invalid camp session price.")
    payable_cents = max(price_cents, deposit_cents)
    payload = {
        "household_id": student.household_id,
        "registration_source": incoming.get("registration_source") or "EXISTING",
        "form_status": "MISSING",
        "health_status": "NEEDS_REVIEW",
        "pickup_status": "MISSING",
        "payment_status": "DEPOSIT_DUE" if payable_cents else "NOT_BILLED",
        "payment_required_before_attendance": payable_cents > 0,
        "balance_due_cents": payable_cents,
    }

    if SummerCampEnrollment.objects.filter(
        school_id=school_id, student_id=student.id, session_id=session.id,
        status__in=["REGISTERED", "WAITLISTED"],
    ).exists():
        raise ValueError("Camper is already registered or waitlisted in this session.")

    state = compute_session_capacity(school_id, session.id)
    if not state.has_open_capacity and state.waitlisted_count >= session.waitlist_capacity:
        raise ValueError("Camp session and waitlist have no remaining capacity.")
    status = "REGISTERED" if state.has_open_capacity else "WAITLISTED"
    waitlist_position = None if status == "REGISTERED" else _next_waitlist_position(school_id, session.id)

    enrollment = SummerCampEnrollment.objects.create(
        school_id=school_id,
        student_id=student.id,
        session_id=session.id,
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


def camp_school_local_date(school_id, stamp):
    """Use the school's civil day for custody; misconfigured timezones fail closed."""
    from core.models import School

    if timezone.is_naive(stamp):
        raise ValueError("Camp custody timestamps must contain timezone information.")
    name = (
        School.objects.filter(pk=school_id, is_active=True)
        .values_list("timezone", flat=True)
        .first()
    )
    if not name:
        raise ValueError("An active school with a timezone is required for Camp.")
    try:
        return stamp.astimezone(ZoneInfo(name)).date()
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError("A valid school timezone is required for Camp.") from exc


@transaction.atomic
def checkin_camper(school_id, student_id, session_id, when=None, note=""):
    """Admit only a currently cleared camper into an active school-owned session."""
    when = when or timezone.now()
    attendance_day = camp_school_local_date(school_id, when)
    session = SummerCampSession.objects.select_for_update().filter(
        id=session_id, school_id=school_id, status="PUBLISHED",
        start_date__lte=attendance_day, end_date__gte=attendance_day,
    ).first()
    if session is None:
        raise ValueError("Camp session is not available for check-in.")

    # Serialize all Camp admissions for the same child across sessions and
    # school-local dates, not just the unique row for one session/day.
    student = Student.objects.select_for_update().filter(
        pk=student_id, school_id=school_id, is_active=True,
    ).first()
    if student is None:
        raise ValueError("Camper does not have exactly one active registration for this session.")

    # Checkout already requires a unique current registration; admission
    # must not pick an arbitrary row from ambiguous legacy enrollments.
    active = list(
        SummerCampEnrollment.objects.select_for_update().filter(
            school_id=school_id, session_id=session.id, student_id=student_id,
            student__school_id=school_id, student__is_active=True,
            status="REGISTERED",
        ).order_by("pk")[:2]
    )
    if len(active) != 1:
        raise ValueError("Camper does not have exactly one active registration for this session.")
    enrollment = active[0]

    # Recompute rather than trusting a readiness value cached at enrollment.
    readiness = compute_camper_readiness(school_id, enrollment.id)
    if readiness["status"] != "READY":
        raise ValueError("Camper is not cleared for check-in.")

    if SummerCampAttendance.objects.filter(
        school_id=school_id, session_id=session.id,
        student_id=student_id, date=attendance_day,
    ).exists():
        raise ValueError("Camper has already been checked in for this session and date.")

    if SummerCampAttendance.objects.filter(
        school_id=school_id, student_id=student_id,
        checkout_time__isnull=True,
    ).exists():
        raise ValueError("An unresolved camp custody record must be reconciled before new check-in.")

    return SummerCampAttendance.objects.create(
        school_id=school_id, student_id=student_id, session_id=session.id,
        date=attendance_day, checkin_time=when, notes=note,
    )


@transaction.atomic
def checkout_camper(
    school_id,
    student_id,
    session_id,
    pickup_contact_id=None,
    pickup_verified=False,
    when=None,
    verified_by=None,
):
    """Release a camper only to an authorized contact with attributable staff approval."""
    from core.models import School
    from core.permissions import user_has_permission

    if pickup_verified is not True:
        raise ValueError("Pickup identity must be verified before checkout.")
    if type(pickup_contact_id) is not int or pickup_contact_id <= 0:
        raise ValueError("An active authorized pickup contact is required.")
    if not verified_by or not getattr(verified_by, "is_authenticated", False):
        raise ValueError("A school-authorized staff verifier is required.")
    if not getattr(verified_by, "is_active", False) or getattr(verified_by, "school_id", None) != school_id:
        raise ValueError("A school-authorized staff verifier is required.")
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None or not user_has_permission(verified_by, "summer_camp.edit", school=school):
        raise ValueError("A school-authorized staff verifier is required.")

    when = when or timezone.now()
    checkout_day = camp_school_local_date(school_id, when)
    # The requested session must actually belong to this school, including
    # when historical enrollment or attendance rows have inconsistent tenant FKs.
    # Lock session before student, matching check-in's lock acquisition order.
    session = SummerCampSession.objects.select_for_update().filter(
        pk=session_id, school_id=school_id,
    ).first()
    if session is None:
        raise ValueError("Camp session does not belong to this school.")
    # Share the same child-level lock as check-in, serializing admission and
    # release across sessions and local dates. Do not require an active
    # enrollment/student status to finish a previously started custody record.
    child = Student.objects.select_for_update().filter(
        pk=student_id, school_id=school_id,
    ).first()
    if child is None:
        raise ValueError("A matching camp check-in is required before checkout.")
    # Never choose an arbitrary open row from inconsistent legacy records.
    # A prior LOCAL day may be released normally after identity verification;
    # older/future-dated or multiply-open custody requires supervisor review.
    open_records = list(
        SummerCampAttendance.objects.select_for_update().filter(
            school_id=school_id, student_id=student_id,
            checkout_time__isnull=True,
        ).order_by("-date", "-pk")[:2]
    )
    if len(open_records) > 1:
        raise ValueError("Multiple open camp custody records require supervisor reconciliation.")
    if not open_records:
        if SummerCampAttendance.objects.filter(
            school_id=school_id, student_id=student_id, session_id=session_id,
            date__in=(checkout_day, checkout_day - timedelta(days=1)),
            checkout_time__isnull=False,
        ).exists():
            raise ValueError("Camper has already been checked out.")
        raise ValueError("A matching camp check-in is required before checkout.")

    attendance = open_records[0]
    if attendance.session_id != session.id or attendance.session.school_id != school_id:
        raise ValueError("Open camp custody belongs to a different session or school.")
    if attendance.date not in (checkout_day, checkout_day - timedelta(days=1)):
        raise ValueError("Older camp custody requires supervisor reconciliation.")
    if camp_school_local_date(school_id, attendance.checkin_time) != attendance.date:
        raise ValueError("Camp check-in date mismatch requires supervisor reconciliation.")
    if when < attendance.checkin_time:
        raise ValueError("Checkout cannot precede check-in.")

    # Contacts belong to a particular enrollment. A cancelled enrollment's
    # contact cannot authorize release after the child is re-registered.
    # Fail closed if no unique current registration exists; legacy data may
    # contain more than one REGISTERED enrollment for the same child/session.
    active_enrollment_ids = list(
        SummerCampEnrollment.objects.select_for_update()
        .filter(
            school_id=school_id,
            session_id=session_id,
            student_id=student_id,
            status="REGISTERED",
        )
        .values_list("id", flat=True)[:2]
    )
    if len(active_enrollment_ids) != 1:
        raise ValueError("One active camp registration is required for checkout.")

    pickup_contact = SummerCampPickupContact.objects.filter(
        pk=pickup_contact_id,
        is_active=True,
        school_id=school_id,
        enrollment_id=active_enrollment_ids[0],
    ).first()
    if pickup_contact is None:
        raise ValueError("Pickup contact is not authorized for this camper and session.")

    attendance.checkout_time = when
    attendance.pickup_contact = pickup_contact
    attendance.pickup_verified = True
    attendance.pickup_verified_by = verified_by
    attendance.save(update_fields=["checkout_time", "pickup_contact", "pickup_verified", "pickup_verified_by"])
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


@transaction.atomic
def verify_staff_credentials(school_id, assignment_id, reviewer, evidence_ref):
    """Record an explicit school-authorized, independently reviewed staff qualification.

    This stores a reference to independently checked qualification evidence, not
    the evidence itself. This internal service is not a public verification API.
    A freeform status, reviewer ID, or untrusted client assertion is insufficient.
    """
    from core.models import School
    from core.permissions import user_has_permission

    school = School.objects.filter(pk=school_id, is_active=True).first()
    if (
        school is None
        or reviewer is None
        or not getattr(reviewer, "is_authenticated", False)
        or not getattr(reviewer, "is_active", False)
        or getattr(reviewer, "school_id", None) != school_id
        or not user_has_permission(reviewer, "summer_camp.edit", school=school)
    ):
        raise ValueError("An authorized school credential reviewer is required.")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip() or len(evidence_ref.strip()) > 160:
        raise ValueError("A bounded credential evidence reference is required.")

    assignment = (
        SummerCampStaffAssignment.objects.select_for_update()
        .select_related("staff_user")
        .filter(pk=assignment_id, school_id=school_id, session__school_id=school_id)
        .first()
    )
    if (
        assignment is None
        or not assignment.staff_user.is_active
        or assignment.staff_user.school_id != school_id
    ):
        raise ValueError("An active same-school camp staff assignment is required.")
    if assignment.staff_user_id == reviewer.pk:
        raise ValueError("Staff cannot verify their own camp credential.")
    if assignment.credential_status not in (
        SummerCampStaffAssignment.CREDENTIAL_PENDING,
        SummerCampStaffAssignment.CREDENTIAL_VERIFIED,
        SummerCampStaffAssignment.CREDENTIAL_REVOKED,
    ):
        raise ValueError("Unrecognized staff credential status; manual reconciliation required.")
    reference = evidence_ref.strip()
    if (
        assignment.credential_status == SummerCampStaffAssignment.CREDENTIAL_REVOKED
        and assignment.credential_evidence_ref == reference
    ):
        raise ValueError("Reverification after revocation requires new evidence.")
    assignment.credential_status = SummerCampStaffAssignment.CREDENTIAL_VERIFIED
    assignment.credential_verified_by = reviewer
    assignment.credential_verified_at = timezone.now()
    assignment.credential_evidence_ref = reference
    assignment.save(update_fields=[
        "credential_status", "credential_verified_by",
        "credential_verified_at", "credential_evidence_ref",
    ])
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
    assigned_staff = (
        SummerCampStaffAssignment.objects.filter(
            school_id=school_id, session_id=session_id,
            staff_user__school_id=school_id, staff_user__is_active=True,
            credential_status=SummerCampStaffAssignment.CREDENTIAL_VERIFIED,
            credential_verified_by__school_id=school_id,
            credential_verified_at__isnull=False,
        ).exclude(credential_evidence_ref="").values("staff_user_id").distinct().count()
    )
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
    elif enrollment.status != "REGISTERED":
        blockers.append("BLOCKED")

    if enrollment.payment_required_before_attendance and (
        enrollment.balance_due_cents > 0
        or getattr(enrollment, "payment_status", None) not in ("DEPOSIT_PAID", "PAID_IN_FULL")
    ):
        blockers.append("MISSING_PAYMENT")

    if compute_form_status(school_id, enrollment_id) != "COMPLETE":
        blockers.append("MISSING_FORMS")

    # Do not infer a health-review waiver from an unverified status value.
    # A NOT_REQUIRED exception needs an explicit, authorized policy and audit
    # path; absent that, only approved health clearance can admit a camper.
    if enrollment.health_status != "APPROVED":
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
    """School-civil-day roster plus every open child-custody record.

    Expired sessions, cancelled enrollment and old unresolved check-ins must not
    make a child disappear from an authorized operator's custody view.
    """
    today = camp_school_local_date(school_id, timezone.now())
    enrollments = list(
        SummerCampEnrollment.objects.filter(
            school_id=school_id,
            status="REGISTERED",
            session__start_date__lte=today,
            session__end_date__gte=today,
        ).select_related("session", "student")
    )
    attendance_rows = list(
        SummerCampAttendance.objects.filter(school_id=school_id)
        .filter(Q(date=today) | Q(checkout_time__isnull=True))
        .select_related("session", "student")
        .order_by("date", "pk")
    )
    today_attendance = {}
    open_student_ids = set()
    open_counts = {}
    open_rows = []
    for record in attendance_rows:
        key = (record.session_id, record.student_id)
        if record.date == today:
            today_attendance[key] = record
        if record.checkout_time is None:
            open_rows.append(record)
            # Orphaned custody must remain visible for supervisor handling,
            # but must never suppress unrelated external (student-less) enrollments.
            if record.student_id is not None:
                open_student_ids.add(record.student_id)
                open_counts[record.student_id] = open_counts.get(record.student_id, 0) + 1

    # An earlier unresolved custody takes precedence over a new scheduled
    # arrival. Retain only a UNIQUE current registration for safe identity
    # display; never guess which legacy duplicate enrollment owns a contact.
    registered_for_open = {}
    if open_rows:
        candidate_enrollments = SummerCampEnrollment.objects.filter(
            school_id=school_id, status="REGISTERED",
            session_id__in={row.session_id for row in open_rows},
            student_id__in={row.student_id for row in open_rows if row.student_id},
        ).select_related("session", "student")
        for enrollment in candidate_enrollments:
            key = (enrollment.session_id, enrollment.student_id)
            registered_for_open.setdefault(key, []).append(enrollment)

    def row_for(enrollment, attendance, *, unresolved=False, supervisor=False):
        session = enrollment.session if enrollment else attendance.session
        student = enrollment.student if enrollment else attendance.student
        valid_session = bool(session and session.school_id == school_id)
        valid_student = bool(student and student.school_id == school_id)
        return {
            "enrollment_id": str(enrollment.id) if enrollment else None,
            "session_id": str(session.id) if valid_session else None,
            "session_name": session.name if valid_session else "Unlinked Camp Session",
            "student_id": str(student.id) if valid_student else None,
            "student_name": (
                f"{student.first_name} {student.last_name}" if valid_student else (
                    "External Camper" if enrollment and enrollment.student_id is None else "Unlinked Camper"
                )
            ),
            "status": enrollment.status if enrollment else "UNLINKED_CUSTODY",
            "open_custody_count": open_counts.get(student.id, 0) if valid_student else 0,
            "readiness_status": enrollment.readiness_status if enrollment else "BLOCKED",
            "readiness_blockers": (
                enrollment.readiness_blockers if enrollment else ["UNRESOLVED_CUSTODY"]
            ),
            "checkin_time": attendance.checkin_time.isoformat() if attendance else None,
            "checkout_time": (
                attendance.checkout_time.isoformat()
                if attendance and attendance.checkout_time else None
            ),
            "pickup_verified": bool(attendance.pickup_verified) if attendance else False,
            "form_status": enrollment.form_status if enrollment else None,
            "health_status": enrollment.health_status if enrollment else None,
            "payment_status": enrollment.payment_status if enrollment else None,
            "pickup_status": enrollment.pickup_status if enrollment else None,
            "attendance_id": str(attendance.id) if attendance else None,
            "attendance_date": str(attendance.date) if attendance else None,
            "unresolved_custody": unresolved,
            "requires_supervisor_reconciliation": supervisor,
        }

    rows = []
    for enrollment in enrollments:
        # Open custody from ANY session supersedes all fresh scheduled
        # admissions for this child, even when the enrollment is in another
        # Camp session. Render each open record explicitly below instead.
        if enrollment.student_id in open_student_ids:
            continue
        key = (enrollment.session_id, enrollment.student_id)
        rows.append(row_for(enrollment, today_attendance.get(key)))

    for attendance in open_rows:
        key = (attendance.session_id, attendance.student_id)
        candidates = registered_for_open.get(key, [])
        enrollment = candidates[0] if len(candidates) == 1 else None
        invalid_link = (
            attendance.session.school_id != school_id
            or not attendance.student
            or attendance.student.school_id != school_id
        )
        needs_supervisor = (
            attendance.date < today - timedelta(days=1)
            or attendance.date > today
            or open_counts.get(attendance.student_id, 0) > 1
            or len(candidates) != 1
            or attendance.checkin_time is None
            or invalid_link
        )
        rows.append(row_for(
            enrollment, attendance, unresolved=True,
            supervisor=needs_supervisor,
        ))

    return {
        "date": str(today),
        "rows": rows,
        # Contract used by the verified pickup UI. Count supervisor holds
        # separately from safe current-day attended/releasable rows.
        "unresolved_custody_count": sum(
            1 for row in rows if row["requires_supervisor_reconciliation"]
        ),
    }
