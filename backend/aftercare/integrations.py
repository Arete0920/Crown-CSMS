"""Canonical Aftercare integration seams.

No synthetic IDs or no-op success responses are permitted here. Each hook either
persists the authoritative downstream record or fails closed.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


def _canonical_student(school_id, student_id):
    from households.models import Student

    try:
        return Student.objects.select_related("household").get(pk=student_id, school_id=school_id)
    except Student.DoesNotExist as exc:
        raise ValidationError("Aftercare student is not in the requested school.") from exc


def _payer_for_student(student):
    guardians = list(
        student.household.guardians.filter(
            school_id=student.school_id,
            is_primary=True,
            account__isnull=False,
        ).select_related("account")[:2]
    )
    if len(guardians) != 1:
        raise ValidationError(
            "Aftercare billing requires exactly one primary guardian with an authenticated payer account."
        )
    return guardians[0].account


@transaction.atomic
def create_aftercare_finance_obligation(
    *,
    school_id,
    student_id,
    amount_cents: int,
    description: str,
    reference: str,
) -> int:
    from core.models import School
    from finance.models import FinanceObligation, MoneyStatus, ObligationType

    if amount_cents <= 0:
        raise ValidationError("Aftercare obligation amount must be positive.")
    if not reference or len(reference) > 64:
        raise ValidationError("A valid Aftercare finance reference is required.")

    try:
        school = School.objects.get(pk=school_id)
    except School.DoesNotExist as exc:
        raise ValidationError("Requested school does not exist.") from exc
    student = _canonical_student(school.id, student_id)
    payer = _payer_for_student(student)

    existing = FinanceObligation.objects.select_for_update().filter(
        school=school,
        reference=reference,
    ).first()
    if existing is not None:
        if (
            existing.payer_user_id != payer.id
            or existing.amount_cents != amount_cents
            or existing.description != description
        ):
            raise ValidationError("Existing Aftercare finance reference does not match this charge.")
        return existing.id

    obligation = FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.FEE,
        status=MoneyStatus.OPEN,
        description=description,
        due_date=timezone.localdate(),
        amount_cents=amount_cents,
        currency="USD",
        reference=reference,
    )
    return obligation.id


@transaction.atomic
def create_aftercare_discipline_incident(
    *,
    school_id,
    student_id,
    description: str,
    severity: str,
):
    from core.models import StudentIdentityLink
    from discipline.models import DisciplineAction, DisciplineIncident

    compatibility_student = _canonical_student(school_id, student_id)
    try:
        link = StudentIdentityLink.objects.select_related("core_student", "school").get(
            school_id=school_id,
            compatibility_student=compatibility_student,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
        )
    except StudentIdentityLink.DoesNotExist as exc:
        raise ValidationError(
            "Aftercare discipline escalation requires a verified canonical student identity link."
        ) from exc

    normalized_severity = str(severity).lower()
    if normalized_severity not in {"minor", "moderate", "major"}:
        raise ValidationError("Unsupported discipline severity.")

    incident = DisciplineIncident.objects.create(
        school=link.school,
        student=link.core_student,
        occurred_at=timezone.now(),
        location="Aftercare",
        category="other",
        severity=normalized_severity,
        status="open",
        summary=(f"Aftercare incident ({str(severity).upper()})")[:180],
        details=description,
    )
    DisciplineAction.objects.create(
        incident=incident,
        action_type="created",
        note="Created from canonical Aftercare incident escalation.",
    )
    return incident.id
