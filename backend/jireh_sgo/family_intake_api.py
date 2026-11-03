"""Synthetic-only Jireh SGO APIs; no public enrollment or partner production access."""
import os
from uuid import UUID

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated

from .family_intake import (
    correct_family_application, family_grants, get_family_application, processor_programs,
    processor_queue, request_processor_correction, serialize_intake,
    submit_family_application,
)
from .models import SGOFamilyIntake
from .read_only_api import _reject_school_selector, private


def fictional_intake_enabled():
    """Local, explicit synthetic gate; cannot be turned on in Azure/hosted runtime."""
    return bool(
        getattr(settings, "CROWN_SGO_FICTIONAL_INTAKE_ENABLED", False)
        and getattr(settings, "DEBUG", False)
        and not getattr(settings, "CROWN_DEMO_MODE", False)
        and getattr(settings, "CROWN_ENV", "") == "local"
        and getattr(settings, "DJANGO_ENV", "") == "local"
        and not os.getenv("WEBSITE_HOSTNAME")
        and not os.getenv("WEBSITE_INSTANCE_ID")
        and not os.getenv("AZURE_ENVIRONMENT")
        # Never point the fictional intake flag at a connected production DB.
        and settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    )


def _guard(request):
    _reject_school_selector(request)
    if not fictional_intake_enabled():
        raise NotFound("Fictional SGO intake is unavailable.")


def _payload(request, allowed):
    if not isinstance(request.data, dict):
        raise ValidationError({"detail": "JSON object required."})
    unexpected = set(request.data) - allowed
    if unexpected:
        # Do not echo potentially sensitive, unapproved family field values.
        raise ValidationError({"detail": "Unexpected application field."})
    return request.data


def _program_id(value):
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        raise ValidationError({"program_id": "Opaque program UUID required."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def family_programs(request):
    _guard(request)
    grants = list(family_grants(request.user))
    active = SGOFamilyIntake.objects.filter(grant_id__in=[grant.pk for grant in grants]).values(
        "grant_id", "application_id",
    )
    applications = {row["grant_id"]: str(row["application_id"]) for row in active}
    return private({"programs": [{
        "id": str(grant.program_id),
        "organization_id": str(grant.program.organization_id),
        "organization": grant.program.organization.legal_name,
        "name": grant.program.name,
        "calendar_year": grant.program.calendar_year,
        "policy_version": grant.program.eligibility_rule_version,
        "consent_version": grant.consent_version,
        "application_id": applications.get(grant.id),
    } for grant in grants], "synthetic_only": True, "funds_status": "NONCASH_ONLY"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def family_submit(request):
    _guard(request)
    data = _payload(request, {
        "program_id", "grade_level", "consent", "consent_version", "submission_key",
    })
    intake, created = submit_family_application(
        user=request.user, program_id=_program_id(data.get("program_id")),
        grade_level=data.get("grade_level"), consent=data.get("consent"),
        consent_version=data.get("consent_version"), submission_key=data.get("submission_key"),
    )
    response = private({"application": serialize_intake(intake), "created": created})
    response.status_code = 201 if created else 200
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def family_application(request, application_id):
    _guard(request)
    intake = get_family_application(user=request.user, application_id=application_id)
    return private({"application": serialize_intake(intake)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def family_correct(request, application_id):
    _guard(request)
    data = _payload(request, {"expected_revision", "grade_level", "correction_key"})
    intake, changed = correct_family_application(
        user=request.user, application_id=application_id,
        expected_revision=data.get("expected_revision"),
        grade_level=data.get("grade_level"),
        correction_key=data.get("correction_key"),
    )
    return private({"application": serialize_intake(intake), "changed": changed})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def processor_program_list(request):
    _guard(request)
    assignments = list(processor_programs(request.user))
    return private({"programs": [{
        "id": str(item.program_id), "name": item.program.name,
        "organization": item.program.organization.legal_name,
        "organization_id": str(item.program.organization_id),
    } for item in assignments], "authority": "PROCESSOR_VERIFICATION_ONLY",
       "funds_status": "NONCASH_ONLY"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def processor_application_queue(request, program_id):
    _guard(request)
    rows = processor_queue(user=request.user, program_id=program_id)
    return private({"applications": [serialize_intake(intake, authority="PROCESSOR_VERIFICATION_ONLY") for intake in rows],
                    "program_id": str(program_id), "authority": "PROCESSOR_VERIFICATION_ONLY",
                    "funds_status": "NONCASH_ONLY"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def processor_request_correction(request, application_id):
    _guard(request)
    data = _payload(request, {"expected_revision", "reason", "request_key"})
    intake, changed = request_processor_correction(
        user=request.user, application_id=application_id,
        expected_revision=data.get("expected_revision"),
        reason=data.get("reason"), request_key=data.get("request_key"),
    )
    return private({"application": serialize_intake(intake, authority="PROCESSOR_VERIFICATION_ONLY"), "changed": changed})
