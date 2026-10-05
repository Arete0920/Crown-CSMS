from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone


class HomeAcademyIntegrationError(ValueError):
    """Raised when a downstream Home Academy integration cannot be proven safe."""


def _to_cents(amount) -> int:
    value = (Decimal(amount) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(value)


def _resolve_payer_user(*, school_id, student_id):
    from core.models import Student, UserAccount

    student = (
        Student.objects.select_related("family")
        .filter(pk=student_id, school_id=school_id, status="ACTIVE")
        .first()
    )
    if student is None:
        raise HomeAcademyIntegrationError("Canonical student is not active in this school.")

    payers = list(
        UserAccount.objects.filter(
            school_id=school_id,
            guardian__school_id=school_id,
            guardian__family_id=student.family_id,
            guardian__portal_access=True,
            is_active=True,
        ).select_related("guardian")[:2]
    )
    if len(payers) != 1:
        raise HomeAcademyIntegrationError(
            "Exactly one active portal guardian payer is required before Home Academy billing."
        )
    return student, payers[0]


@transaction.atomic
def create_finance_obligation_for_registration(registration):
    """
    Create and ledger-post the canonical finance obligation for a Home Academy registration.

    Idempotent: an existing finance_obligation_id is returned unchanged.
    Zero-priced offerings create no obligation and return None.
    """
    from finance.models import FinanceObligation, ObligationType
    from finance.services import ledger_post_obligation
    from home_academy.models import OfferingEnrollment

    locked = (
        OfferingEnrollment.objects.select_for_update()
        .select_related("offering")
        .get(pk=registration.pk)
    )
    if locked.finance_obligation_id:
        obligation = FinanceObligation.objects.filter(
            pk=locked.finance_obligation_id,
            school_id=locked.school_id,
        ).first()
        if obligation is None:
            raise HomeAcademyIntegrationError(
                "Stored Home Academy finance obligation reference is invalid."
            )
        return obligation

    offering = locked.offering
    if offering.school_id != locked.school_id:
        raise HomeAcademyIntegrationError("Offering tenant does not match registration tenant.")

    amount_cents = _to_cents(offering.price)
    if amount_cents <= 0:
        locked.payment_status = "not_required"
        locked.save(update_fields=["payment_status", "updated_at"])
        return None

    student, payer = _resolve_payer_user(
        school_id=locked.school_id,
        student_id=locked.student_id,
    )

    obligation = FinanceObligation.objects.create(
        school_id=locked.school_id,
        payer_user=payer,
        obligation_type=ObligationType.FEE,
        description=f"Home Academy: {offering.title}",
        due_date=timezone.localdate(),
        amount_cents=amount_cents,
        academic_year_label=offering.school_year,
        reference=f"home-academy:{locked.pk}",
    )
    result = ledger_post_obligation(obligation)
    if not result.ok:
        raise HomeAcademyIntegrationError(
            f"Home Academy ledger posting failed: {result.reference}"
        )

    locked.finance_obligation_id = obligation.pk
    locked.payment_status = "pending"
    locked.save(update_fields=["finance_obligation_id", "payment_status", "updated_at"])
    return obligation



@transaction.atomic
def post_transcript_for_registration(registration):
    """
    Post one official transcript entry only after all Home Academy registrar guardrails pass.

    Requires a verified canonical-to-compatibility student identity link, canonical
    academic course/term references, school-of-record status, an active transcript
    rule, and completed grade evidence. Existing transcript rows are never overwritten.
    """
    from academics.models import Course, Term, TranscriptEntry
    from core.models import StudentIdentityLink
    from home_academy.models import OfferingEnrollment, TranscriptPostingRule

    locked = (
        OfferingEnrollment.objects.select_for_update()
        .select_related("offering", "offering__program", "home_academy_enrollment")
        .get(pk=registration.pk)
    )

    if locked.transcript_entry_id:
        existing = TranscriptEntry.objects.filter(
            pk=locked.transcript_entry_id,
            school_id=locked.school_id,
        ).first()
        if existing is None:
            raise HomeAcademyIntegrationError(
                "Stored Home Academy transcript reference is invalid."
            )
        return existing

    if locked.status != "completed":
        raise HomeAcademyIntegrationError(
            "Registration must be completed before transcript posting."
        )

    offering = locked.offering
    if not offering.credit_bearing or not offering.transcript_eligible:
        raise HomeAcademyIntegrationError(
            "Offering is not approved for transcript credit."
        )

    enrollment = locked.home_academy_enrollment
    if enrollment is None or enrollment.school_id != locked.school_id:
        raise HomeAcademyIntegrationError(
            "A same-school Home Academy enrollment is required."
        )
    if enrollment.student_id != locked.student_id:
        raise HomeAcademyIntegrationError(
            "Home Academy enrollment student does not match registration."
        )
    if not enrollment.is_school_of_record:
        raise HomeAcademyIntegrationError(
            "School-of-record status is required for official transcript posting."
        )

    rule = TranscriptPostingRule.objects.filter(
        offering=offering,
        active=True,
    ).first()
    if rule is None:
        raise HomeAcademyIntegrationError(
            "An active transcript posting rule is required."
        )
    if rule.requires_registrar_approval is False:
        raise HomeAcademyIntegrationError(
            "Transcript rule must retain registrar approval."
        )
    if rule.credit_value <= 0:
        raise HomeAcademyIntegrationError(
            "Transcript credit value must be greater than zero."
        )
    if not locked.final_letter_grade:
        raise HomeAcademyIntegrationError(
            "Final letter grade is required before transcript posting."
        )
    if not offering.academic_course_id:
        raise HomeAcademyIntegrationError(
            "Canonical academic course mapping is required."
        )

    course = Course.objects.filter(
        pk=offering.academic_course_id,
        school_id=locked.school_id,
    ).first()
    if course is None:
        raise HomeAcademyIntegrationError(
            "Mapped academic course was not found in this school."
        )

    term = None
    if offering.academic_term_id:
        term = Term.objects.filter(
            pk=offering.academic_term_id,
            school_id=locked.school_id,
        ).first()
        if term is None:
            raise HomeAcademyIntegrationError(
                "Mapped academic term was not found in this school."
            )

    link = (
        StudentIdentityLink.objects.select_related("compatibility_student")
        .filter(
            school_id=locked.school_id,
            core_student_id=locked.student_id,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            compatibility_student__school_id=locked.school_id,
            compatibility_student__is_active=True,
        )
        .exclude(evidence_reference="")
        .first()
    )
    if link is None or not link.evidence_reference.strip():
        raise HomeAcademyIntegrationError(
            "Verified student identity mapping is required for transcript posting."
        )

    collision = TranscriptEntry.objects.filter(
        student=link.compatibility_student,
        course=course,
        term=term,
    ).first()
    if collision is not None:
        raise HomeAcademyIntegrationError(
            "An official transcript entry already exists for this student/course/term."
        )

    entry = TranscriptEntry.objects.create(
        school_id=locked.school_id,
        student=link.compatibility_student,
        course=course,
        term=term,
        credit_value=rule.credit_value,
        final_letter_grade=locked.final_letter_grade,
        final_percentage=locked.final_percentage,
        provider=(
            offering.program.public_program_name
            if offering.program_id
            else "Home Academy"
        ),
    )
    locked.transcript_entry_id = entry.id
    locked.transcript_posting_status = "posted"
    locked.save(
        update_fields=[
            "transcript_entry_id",
            "transcript_posting_status",
            "updated_at",
        ]
    )
    return entry
