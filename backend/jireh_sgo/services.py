"""Explicit SGO membership and noncash workflows; no payment or school-aid imports."""
import re
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import SGOApplication, SGOAuditEvent, SGOAward, SGOMembership, SGOProgram

POLICY_REF = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def membership_for(user, organization_id, *, roles=None):
    if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        raise PermissionDenied("Active SGO membership required.")
    member = SGOMembership.objects.select_related("organization").filter(
        organization_id=organization_id, user=user, active=True, organization__active=True,
    ).first()
    if member is None or (roles is not None and member.role not in roles):
        raise PermissionDenied("Active SGO membership required.")
    return member


def _audit(*, organization, actor, action, subject_key, metadata=None):
    return SGOAuditEvent.objects.create(
        organization=organization, actor=actor, action=action,
        subject_key=subject_key, metadata={} if metadata is None else metadata,
    )


def _uuid(value, field):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({field: "Opaque UUID required."})


@transaction.atomic
def create_program(*, user, organization_id, name, code, calendar_year, funding_source, rule_version):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN})
    if funding_source not in dict(SGOProgram.SOURCES):
        raise ValidationError({"funding_source": "Unsupported source."})
    if type(calendar_year) is not int or not 2026 <= calendar_year <= 2100:
        raise ValidationError({"calendar_year": "Invalid year."})
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise ValidationError({"name": "Invalid name."})
    if not isinstance(code, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,69}", code):
        raise ValidationError({"code": "Invalid code."})
    if not isinstance(rule_version, str) or not POLICY_REF.fullmatch(rule_version):
        raise ValidationError({"rule_version": "Opaque version reference required."})
    program, created = SGOProgram.objects.get_or_create(
        organization=member.organization, code=code, calendar_year=calendar_year,
        eligibility_rule_version=rule_version,
        defaults={"name": name, "funding_source": funding_source},
    )
    if program.name != name or program.funding_source != funding_source:
        raise ValidationError({"code": "Version already exists with different attributes."})
    if created:
        _audit(organization=member.organization, actor=user, action=SGOAuditEvent.PROGRAM_CREATED,
               subject_key=program.id, metadata={"source": funding_source, "year": calendar_year})
    return program


@transaction.atomic
def create_application(*, user, organization_id, program_id, student_key, school_key):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN, SGOMembership.REVIEWER})
    program = SGOProgram.objects.filter(id=program_id, organization=member.organization).first()
    if program is None:
        raise PermissionDenied("SGO program unavailable.")
    student_key, school_key = _uuid(student_key, "student_key"), _uuid(school_key, "school_key")
    application, created = SGOApplication.objects.get_or_create(
        program=program, student_key=student_key, defaults={"school_key": school_key},
    )
    if application.school_key != school_key:
        raise ValidationError({"school_key": "Conflicting school reference."})
    if created:
        _audit(organization=member.organization, actor=user,
               action=SGOAuditEvent.APPLICATION_CREATED, subject_key=application.id)
    return application


@transaction.atomic
def attest_eligibility(*, user, organization_id, application_id, eligible, evidence_key):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN, SGOMembership.REVIEWER})
    if type(eligible) is not bool:
        raise ValidationError({"eligible": "Reviewer decision must be a boolean."})
    evidence_key = _uuid(evidence_key, "evidence_key")
    if evidence_key.version != 4:
        raise ValidationError({"evidence_key": "Generated opaque UUID4 evidence reference required."})
    application = SGOApplication.objects.select_for_update().filter(
        id=application_id, program__organization=member.organization,
    ).first()
    if application is None:
        raise PermissionDenied("SGO application unavailable.")
    if SGOAward.objects.filter(application=application).exists():
        raise ValidationError({"application_id": "Eligibility locked after commitment."})
    decision = SGOApplication.ELIGIBLE if eligible else SGOApplication.INELIGIBLE
    if application.eligibility == decision and application.reviewer_evidence_key == evidence_key:
        return application
    application.eligibility = decision
    application.reviewer_evidence_key = evidence_key
    application.reviewed_by = user
    application.reviewed_at = timezone.now()
    application.save(update_fields=["eligibility", "reviewer_evidence_key", "reviewed_by", "reviewed_at"])
    _audit(organization=member.organization, actor=user,
           action=SGOAuditEvent.ELIGIBILITY_ATTESTED, subject_key=application.id,
           metadata={"outcome": decision})
    return application


@transaction.atomic
def commit_award(*, user, organization_id, application_id, amount_cents):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN})
    if type(amount_cents) is not int or not 0 < amount_cents <= 9_000_000_000_000_000:
        raise ValidationError({"amount_cents": "Positive integer cents required."})
    application = SGOApplication.objects.select_for_update().filter(
        id=application_id, program__organization=member.organization,
    ).first()
    if application is None:
        raise PermissionDenied("SGO application unavailable.")
    if application.eligibility != SGOApplication.ELIGIBLE or not application.reviewer_evidence_key:
        raise ValidationError({"application_id": "Human eligibility attestation required."})
    existing = SGOAward.objects.filter(application=application).first()
    if existing:
        if existing.status == SGOAward.COMMITTED and existing.amount_cents == amount_cents:
            return existing
        raise ValidationError({"application_id": "Commitment cannot change or revive."})
    award = SGOAward.objects.create(
        application=application, amount_cents=amount_cents, authorized_by=user,
    )
    _audit(organization=member.organization, actor=user, action=SGOAuditEvent.AWARD_COMMITTED,
           subject_key=award.id, metadata={"amount_cents": amount_cents})
    return award


@transaction.atomic
def cancel_award(*, user, organization_id, award_id):
    member = membership_for(user, organization_id, roles={SGOMembership.ADMIN})
    award = SGOAward.objects.select_for_update().filter(
        id=award_id, application__program__organization=member.organization,
    ).first()
    if award is None:
        raise PermissionDenied("SGO award unavailable.")
    if award.status == SGOAward.CANCELLED:
        return award
    award.status = SGOAward.CANCELLED
    award.save(update_fields=["status"])
    _audit(organization=member.organization, actor=user,
           action=SGOAuditEvent.AWARD_CANCELLED, subject_key=award.id)
    return award
