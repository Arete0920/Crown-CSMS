"""Fail-closed SGO authorization and noncash application/award workflows."""
import re
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import (
    SGOApplication, SGOAuditEvent, SGOAward, SGOMembership,
    SGOOrganization, SGOProgram,
)

OPAQUE_EVIDENCE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def membership_for(user, organization_id, *, roles=None):
    if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        raise PermissionDenied("SGO membership required.")
    # Staff/superuser status does NOT override explicit membership.
    member = SGOMembership.objects.select_related("organization").filter(
        organization_id=organization_id,
        user=user,
        active=True,
        organization__active=True,
    ).first()
    if member is None or (roles is not None and member.role not in roles):
        raise PermissionDenied("SGO membership required.")
    return member


def audit(*, organization, actor, action, subject_key, metadata=None):
    # Only non-PII metadata may be recorded.
    return SGOAuditEvent.objects.create(
        organization=organization, actor=actor, action=action,
        subject_key=subject_key, metadata=metadata or {},
    )


def create_program(*, user, organization_id, name, code, calendar_year, funding_source, rule_version):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN})
    if funding_source not in dict(SGOProgram.SOURCES):
        raise ValidationError({"funding_source": "Unsupported program source."})
    if not name or not code or not rule_version:
        raise ValidationError({"detail": "Name, code and approved rule-version reference are required."})
    if not (2026 <= calendar_year <= 2100) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,69}", code):
        raise ValidationError({"detail": "Invalid calendar year or program code."})
    if not OPAQUE_EVIDENCE.fullmatch(rule_version):
        raise ValidationError({"rule_version": "Provide an opaque approved-policy reference."})
    with transaction.atomic():
        try:
            program = SGOProgram.objects.create(
                organization=member.organization, name=name, code=code,
                calendar_year=calendar_year, funding_source=funding_source,
                eligibility_rule_version=rule_version,
                status=SGOProgram.PILOT,
            )
        except IntegrityError:
            raise ValidationError({"code": "Program code already exists for this organization and year."})
        audit(organization=member.organization, actor=user, action="PROGRAM_CREATED",
              subject_key=program.id, metadata={"source": funding_source, "year": calendar_year})
    return program


def create_application(*, user, organization_id, program_id, student_key, school_key):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN, SGOMembership.REVIEWER})
    program = SGOProgram.objects.filter(id=program_id, organization=member.organization).first()
    if program is None:
        raise ValidationError({"program_id": "Program does not belong to this SGO."})
    if program.status != SGOProgram.PILOT:
        raise ValidationError({"program_id": "This foundation supports pilot-only intake."})
    try:
        student_key, school_key = UUID(str(student_key)), UUID(str(school_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({"detail": "Opaque student_key and school_key UUIDs are required."})
    with transaction.atomic():
        try:
            application = SGOApplication.objects.create(
                organization=member.organization, program=program,
                student_key=student_key, school_key=school_key,
            )
        except IntegrityError:
            raise ValidationError({"student_key": "Application already exists for this program and student."})
        audit(organization=member.organization, actor=user, action="APPLICATION_CREATED",
              subject_key=application.id)
    return application


@transaction.atomic
def attest_eligibility(*, user, organization_id, application_id, eligible, evidence_key):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN, SGOMembership.REVIEWER})
    if not isinstance(eligible, bool):
        raise ValidationError({"eligible": "A true or false reviewer decision is required."})
    if not isinstance(evidence_key, str) or not OPAQUE_EVIDENCE.fullmatch(evidence_key):
        raise ValidationError({"evidence_key": "An opaque evidence reference is required."})
    application = SGOApplication.objects.select_for_update().filter(
        id=application_id, organization=member.organization, program__organization=member.organization,
    ).first()
    if application is None:
        raise ValidationError({"application_id": "Unknown application for this SGO."})
    if SGOAward.objects.filter(application=application).exists():
        raise ValidationError({"application_id": "Awards must be reviewed before eligibility can change."})
    application.eligibility = SGOApplication.ELIGIBLE if eligible else SGOApplication.INELIGIBLE
    application.reviewer_evidence_key = evidence_key
    application.reviewed_by = user
    application.reviewed_at = timezone.now()
    application.save(update_fields=["eligibility", "reviewer_evidence_key", "reviewed_by", "reviewed_at"])
    audit(organization=member.organization, actor=user, action="ELIGIBILITY_ATTESTED",
          subject_key=application.id, metadata={"outcome": application.eligibility})
    return application


@transaction.atomic
def commit_award(*, user, organization_id, application_id, amount_cents):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN})
    if type(amount_cents) is not int or not (0 < amount_cents <= 9_000_000_000_000_000):
        raise ValidationError({"amount_cents": "A positive integer cents amount is required."})
    application = SGOApplication.objects.select_for_update().filter(
        id=application_id, organization=member.organization, program__organization=member.organization,
    ).first()
    if application is None:
        raise ValidationError({"application_id": "Unknown application for this SGO."})
    if application.program.status != SGOProgram.PILOT:
        raise ValidationError({"application_id": "Pilot-only award commitments are supported."})
    if application.eligibility != SGOApplication.ELIGIBLE or not application.reviewer_evidence_key:
        raise ValidationError({"application_id": "Verified reviewer eligibility attestation required."})
    if SGOAward.objects.filter(application=application).exists():
        raise ValidationError({"application_id": "An award commitment already exists."})
    award = SGOAward.objects.create(
        organization=member.organization, application=application,
        amount_cents=amount_cents, authorized_by=user,
    )
    audit(organization=member.organization, actor=user, action="AWARD_COMMITTED_NONCASH",
          subject_key=award.id, metadata={"amount_cents": amount_cents})
    return award
