from dataclasses import dataclass

from .models import FinancialAidRule, HomeAcademyEnrollment, Offering, OfferingEnrollment


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    failures: list[str]
    seats_remaining: int
    waitlist_available: bool


def count_active_academic_courses(school_id: int, student_id: int, school_year: str = "", term: str = "") -> int:
    """Count active/approved credit-bearing academic course enrollments for the student."""
    qs = OfferingEnrollment.objects.filter(
        school_id=school_id,
        student_id=student_id,
        status__in=["approved", "active", "completed"],
        offering__offering_type="academic_course",
        offering__credit_bearing=True,
        offering__active=True,
    )
    if school_year:
        qs = qs.filter(offering__school_year=school_year)
    if term:
        qs = qs.filter(offering__term=term)
    return qs.count()


def count_home_academy_roster_seats(offering: Offering) -> int:
    """Count homeschool roster seats already consumed for an offering."""
    return OfferingEnrollment.objects.filter(
        school_id=offering.school_id,
        offering=offering,
        status__in=["eligible", "approved", "active", "completed"],
    ).count()


def homeschool_seats_remaining(offering: Offering) -> int:
    """
    Calculate remaining homeschool seats released by the school.

    A homeschool_seat_cap of 0 means no homeschool seats have been released.
    The total classroom capacity still protects full-time reserved and buffer seats.
    """
    used = count_home_academy_roster_seats(offering)
    released_cap = max(offering.homeschool_seat_cap, 0)

    if offering.total_capacity:
        physical_limit = max(
            offering.total_capacity - offering.reserved_full_time_seats - offering.buffer_seats,
            0,
        )
        released_cap = min(released_cap, physical_limit)

    return max(released_cap - used, 0)


def get_home_academy_enrollment(school_id: int, student_id: int) -> HomeAcademyEnrollment | None:
    return (
        HomeAcademyEnrollment.objects.filter(
            school_id=school_id,
            student_id=student_id,
            is_active=True,
        )
        .order_by("-created_at")
        .first()
    )


def evaluate_offering_eligibility(
    *,
    school_id: int,
    student_id: int,
    offering: Offering,
    forms_complete: bool = False,
    account_current: bool = True,
    admin_approved: bool = False,
    coach_or_director_approved: bool = False,
) -> EligibilityResult:
    """Evaluate Home Academy enrollment gates for one student/offering."""
    failures: list[str] = []
    enrollment = get_home_academy_enrollment(school_id=school_id, student_id=student_id)

    if not enrollment:
        failures.append("Active Home Academy affiliation is required.")

    if offering.blocks_if_forms_missing and not forms_complete:
        failures.append("Required Home Academy forms are incomplete.")

    if offering.blocks_if_past_due and not account_current:
        failures.append("Account must be current before registration.")

    if offering.requires_school_of_record:
        if not enrollment or not enrollment.is_school_of_record:
            failures.append("School-of-record status is required for this offering.")

    if offering.requires_academic_anchor and offering.min_academic_courses_required:
        if enrollment and enrollment.is_school_of_record:
            academic_count = offering.min_academic_courses_required
        elif enrollment and enrollment.is_diploma_track:
            academic_count = offering.min_academic_courses_required
        else:
            academic_count = count_active_academic_courses(
                school_id=school_id,
                student_id=student_id,
                school_year=offering.school_year,
                term=offering.term,
            )
        if academic_count < offering.min_academic_courses_required:
            failures.append(
                f"Requires at least {offering.min_academic_courses_required} approved academic course(s)."
            )

    if offering.requires_admin_approval and not admin_approved:
        failures.append("Administrator approval is required.")

    if offering.requires_coach_or_director_approval and not coach_or_director_approved:
        failures.append("Coach or director approval is required.")

    seats_remaining = homeschool_seats_remaining(offering)
    waitlist_available = bool(offering.waitlist_enabled)
    if seats_remaining <= 0:
        failures.append("No homeschool affiliate seats are currently available.")

    return EligibilityResult(
        eligible=len(failures) == 0,
        failures=failures,
        seats_remaining=seats_remaining,
        waitlist_available=waitlist_available,
    )


def apply_eligibility_to_registration(registration: OfferingEnrollment) -> OfferingEnrollment:
    """Evaluate and persist eligibility status for a pending offering registration."""
    result = evaluate_offering_eligibility(
        school_id=registration.school_id,
        student_id=registration.student_id,
        offering=registration.offering,
        forms_complete=registration.form_status in {"complete", "not_required"},
        account_current=registration.payment_status not in {"past_due"},
        admin_approved=registration.admin_approved,
        coach_or_director_approved=registration.coach_or_director_approved,
    )
    registration.eligibility_failures = result.failures
    registration.eligibility_status = "eligible" if result.eligible else "blocked"
    if result.eligible:
        registration.status = "eligible"
        registration.roster_status = "eligible"
    elif result.seats_remaining <= 0 and result.waitlist_available:
        registration.status = "waitlisted"
        registration.roster_status = "waitlisted"
    else:
        registration.status = "pending_eligibility"
        registration.roster_status = "blocked"
    registration.save(update_fields=[
        "eligibility_failures",
        "eligibility_status",
        "status",
        "roster_status",
        "updated_at",
    ])
    return registration


AID_CHARGE_TYPE_BY_OFFERING = {
    "academic_course": "course_fee",
    "lab": "lab_fee",
    "sport": "athletic_fee",
    "music": "activity_fee",
    "drama": "activity_fee",
    "art": "activity_fee",
    "club": "activity_fee",
    "student_life": "activity_fee",
    "testing": "testing_fee",
    "transcript_review": "transcript_fee",
    "graduation_audit": "graduation_audit_fee",
}


def classify_financial_aid(registration: OfferingEnrollment) -> OfferingEnrollment:
    """Persist charge-level financial-aid classification from school-controlled rules."""
    charge_type = AID_CHARGE_TYPE_BY_OFFERING.get(registration.offering.offering_type)
    rule = None
    if charge_type:
        rule = FinancialAidRule.objects.filter(
            school_id=registration.school_id,
            charge_type=charge_type,
            active=True,
        ).first()

    registration.financial_aid_rule_id = rule.pk if rule else None
    registration.aid_eligible = bool(rule and rule.aid_eligible)
    registration.save(
        update_fields=["financial_aid_rule_id", "aid_eligible", "updated_at"]
    )
    return registration
