"""Local synthetic Jireh SGO family intake and delegated processor case actions.

Separate trust domain: family grants and processor assignments never inherit
SGO membership, superuser, school role, or tenant context. No real documents,
fund movement, eligibility determination, or partner decisions are performed.
"""
from uuid import UUID

from django.db import transaction
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from .models import (
    SGOApplication, SGOAuditEvent, SGOAward, SGOFamilyGrant, SGOFamilyIntake,
    SGOProcessorAssignment,
)
from .services import _audit


class IntakeConflict(APIException):
    status_code = 409
    default_detail = "Intake revision conflict."
    default_code = "sgo_intake_conflict"


def _uuid4(value, field):
    try:
        parsed = UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({field: "A generated UUID4 idempotency key is required."})
    if parsed.version != 4:
        raise ValidationError({field: "A generated UUID4 idempotency key is required."})
    return parsed


def _revision(value):
    if type(value) is not int or value < 1:
        raise ValidationError({"expected_revision": "Positive integer revision required."})
    return value


def _grade(value):
    if not isinstance(value, str) or value not in dict(SGOFamilyIntake.GRADES):
        raise ValidationError({"grade_level": "Select a supported synthetic grade."})
    return value


def _principal(user):
    if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        raise PermissionDenied("An active authorized account is required.")
    return user


def family_grants(user):
    return SGOFamilyGrant.objects.select_related("program", "program__organization").filter(
        user=_principal(user), active=True, program__organization__active=True,
    ).order_by("program__organization__legal_name", "program__name", "id")


def _family_grant(user, program_id, *, lock=False):
    query = family_grants(user)
    if lock:
        query = query.select_for_update()
    grant = query.filter(program_id=program_id).first()
    if grant is None:
        raise PermissionDenied("Fictional partner-program applicant grant required.")
    return grant


def _processor_assignment(user, program_id):
    assignment = SGOProcessorAssignment.objects.select_related("program").filter(
        user=_principal(user), program_id=program_id, active=True,
        program__organization__active=True,
    ).first()
    if assignment is None:
        raise PermissionDenied("Explicit partner-program processor assignment required.")
    return assignment


def serialize_intake(intake):
    """A deliberately minimal, non-PII family/processor readback shape."""
    program = intake.application.program
    return {
        "id": str(intake.application_id),
        "program_id": str(program.id),
        "organization_id": str(program.organization_id),
        "program": program.name,
        "organization": program.organization.legal_name,
        "status": intake.status,
        "revision": intake.revision,
        "grade_level": intake.grade_level,
        "consent_version": intake.consent_version,
        "consented_at": intake.consented_at.isoformat(),
        "submitted_at": intake.submitted_at.isoformat(),
        "correction_reason": (
            intake.requested_reason if intake.status == SGOFamilyIntake.CORRECTION_REQUESTED else None
        ),
        "authority": "SGO_PARTNER_ONLY",
        "funds_status": "NONCASH_ONLY",
    }


@transaction.atomic
def submit_family_application(*, user, program_id, grade_level, consent, consent_version, submission_key):
    grant = _family_grant(user, program_id, lock=True)
    grade = _grade(grade_level)
    key = _uuid4(submission_key, "submission_key")
    if consent is not True or consent_version != grant.consent_version:
        raise ValidationError({"consent": "Explicit acceptance of the assigned program consent is required."})

    current = SGOFamilyIntake.objects.select_related(
        "application__program__organization"
    ).select_for_update().filter(grant=grant).first()
    if current is not None:
        if current.submission_key == key and current.initial_grade_level == grade:
            return current, False
        raise IntakeConflict("An application already exists for this fictional program applicant.")
    if SGOFamilyIntake.objects.filter(submission_key=key).exists():
        raise IntakeConflict("Idempotency key has already been used.")
    # Never silently take ownership of a separately created reviewer application.
    if SGOApplication.objects.filter(program=grant.program, student_key=grant.student_key).exists():
        raise IntakeConflict("Applicant reference already has an application requiring partner review.")

    application = SGOApplication.objects.create(
        program=grant.program, student_key=grant.student_key, school_key=grant.school_key,
    )
    _audit(
        organization=grant.program.organization, actor=user, action=SGOAuditEvent.APPLICATION_CREATED,
        subject_key=application.id,
    )
    intake = SGOFamilyIntake.objects.create(
        application=application, grant=grant, grade_level=grade, initial_grade_level=grade,
        consent_version=grant.consent_version, submission_key=key,
    )
    _audit(
        organization=grant.program.organization, actor=user, action=SGOAuditEvent.INTAKE_SUBMITTED,
        subject_key=application.id, metadata={"revision": intake.revision},
    )
    return intake, True


def get_family_application(*, user, application_id):
    _principal(user)
    intake = SGOFamilyIntake.objects.select_related(
        "application__program__organization", "grant",
    ).filter(
        application_id=application_id, grant__user=user, grant__active=True,
        application__program__organization__active=True,
    ).first()
    if intake is None:
        raise PermissionDenied("Fictional application unavailable.")
    return intake


@transaction.atomic
def correct_family_application(*, user, application_id, expected_revision, grade_level, correction_key):
    _principal(user)
    key = _uuid4(correction_key, "correction_key")
    revision = _revision(expected_revision)
    grade = _grade(grade_level)
    intake = SGOFamilyIntake.objects.select_related(
        "application__program__organization", "grant",
    ).select_for_update().filter(
        application_id=application_id, grant__user=user, grant__active=True,
        application__program__organization__active=True,
    ).first()
    if intake is None:
        raise PermissionDenied("Fictional application unavailable.")
    if (intake.last_correction_key == key
            and intake.status == SGOFamilyIntake.RESUBMITTED
            and intake.revision == revision + 1 and intake.grade_level == grade):
        return intake, False
    if intake.status != SGOFamilyIntake.CORRECTION_REQUESTED or intake.revision != revision:
        raise IntakeConflict("Only a current, explicitly requested correction may be resubmitted.")
    if intake.application.eligibility != SGOApplication.UNREVIEWED or SGOAward.objects.filter(
        application_id=intake.application_id
    ).exists():
        raise IntakeConflict("Cannot amend an eligibility-reviewed or committed application.")
    reason = intake.requested_reason
    intake.status = SGOFamilyIntake.RESUBMITTED
    intake.grade_level = grade
    intake.revision += 1
    intake.last_correction_key = key
    intake.save(update_fields=["status", "grade_level", "revision", "last_correction_key", "updated_at"])
    _audit(
        organization=intake.application.program.organization, actor=user,
        action=SGOAuditEvent.INTAKE_RESUBMITTED, subject_key=intake.application_id,
        metadata={"revision": intake.revision, "reason": reason},
    )
    return intake, True


def processor_programs(user):
    return SGOProcessorAssignment.objects.select_related(
        "program", "program__organization"
    ).filter(
        user=_principal(user), active=True, program__organization__active=True,
    ).order_by("program__organization__legal_name", "program__name", "id")


def processor_queue(*, user, program_id):
    assignment = _processor_assignment(user, program_id)
    return SGOFamilyIntake.objects.select_related(
        "application__program__organization", "grant",
    ).filter(application__program=assignment.program).order_by("submitted_at", "id")


@transaction.atomic
def request_processor_correction(
    *, user, application_id, expected_revision, reason, request_key,
):
    _principal(user)
    revision = _revision(expected_revision)
    key = _uuid4(request_key, "request_key")
    if reason not in dict(SGOFamilyIntake.REASONS):
        raise ValidationError({"reason": "Select an approved non-sensitive correction reason."})
    intake = SGOFamilyIntake.objects.select_related(
        "application__program__organization"
    ).select_for_update().filter(application_id=application_id).first()
    if intake is None:
        raise PermissionDenied("Fictional application unavailable.")
    _processor_assignment(user, intake.application.program_id)
    if (intake.last_processor_key == key
            and intake.status == SGOFamilyIntake.CORRECTION_REQUESTED
            and intake.revision == revision + 1 and intake.requested_reason == reason):
        return intake, False
    if intake.status not in (SGOFamilyIntake.SUBMITTED, SGOFamilyIntake.RESUBMITTED):
        raise IntakeConflict("Application is not awaiting a processor verification request.")
    if intake.revision != revision:
        raise IntakeConflict("Application revision changed. Reload before requesting corrections.")
    if intake.application.eligibility != SGOApplication.UNREVIEWED or SGOAward.objects.filter(
        application_id=intake.application_id,
    ).exists():
        raise IntakeConflict("Reviewed or committed applications cannot be changed by a processor.")
    intake.status = SGOFamilyIntake.CORRECTION_REQUESTED
    intake.requested_reason = reason
    intake.last_processor_key = key
    intake.revision += 1
    intake.save(update_fields=["status", "requested_reason", "last_processor_key", "revision", "updated_at"])
    _audit(
        organization=intake.application.program.organization, actor=user,
        action=SGOAuditEvent.INTAKE_CORRECTION_REQUESTED, subject_key=intake.application_id,
        metadata={"revision": intake.revision, "reason": reason},
    )
    return intake, True
