"""Closed local presenter realm using the existing Jireh transaction services."""
from uuid import UUID
from django.core.management.base import CommandError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError
from core.models import UserRole
from households.scoping import get_request_school_id
from aid.family_demo_intake import _linked_family
from aid.hosted_demo_intake import fictional_family_response
from jireh_sgo.family_intake import (family_grants, submit_family_application, get_family_application,
    correct_family_application, processor_programs, processor_queue, request_processor_correction, serialize_intake)
from jireh_sgo.family_intake_api import _payload, _program_id
from jireh_sgo.models import SGOFamilyGrant, SGOFamilyIntake
from jireh_sgo.read_only_api import private
from .catalog import SANDBOX_PERSONAS
from .universal_demo import require_local_presenter, _owned_school
from .universal_identity import presenter_username


def actor_scope(request, roles):
    try:
        require_local_presenter()
        school = _owned_school()
    except CommandError as exc:
        raise NotFound("Not found.") from exc
    user = request.user
    if (school is None or not user.is_active or user.is_staff or user.is_superuser
            or user.school_id != school.pk or get_request_school_id(request) != school.pk):
        raise NotFound("Not found.")
    if any(key in request.query_params for key in ("school_id", "family_id", "organization_id", "workspace_id", "invite_id")):
        raise ValidationError({"detail": "Untrusted presenter selector."})
    if not any(user.username == presenter_username(key) and UserRole.objects.filter(
        school=school, user=user, role_code=SANDBOX_PERSONAS[key].role_code).exists() for key in roles):
        raise NotFound("Not found.")
    return school


def program_scope(request, program_id, *, processor=False):
    school = actor_scope(request, ("finance_director",) if processor else ("parent",))
    # Partner access requires an explicit grant for this fictional school's
    # parent and a verified canonical learner, in addition to processor assignment.
    grants = SGOFamilyGrant.objects.filter(program_id=program_id,
        school_key=school.pk, user__school=school, user__username=presenter_username("parent"), active=True)
    if not grants.exists() or SGOFamilyGrant.objects.filter(program_id=program_id).exclude(school_key=school.pk).exists():
        raise NotFound("Not found.")
    return school


def application_scope(request, application_id, *, processor=False):
    row = SGOFamilyIntake.objects.select_related("application").filter(application_id=application_id).first()
    if row is None:
        raise NotFound("Not found.")
    program_scope(request, row.application.program_id, processor=processor)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def aid_family(request):
    school = actor_scope(request, ("parent",))
    family = _linked_family(request, school.pk)
    if family is None:
        raise NotFound("Not found.")
    return fictional_family_response(request, family, school.pk, source="fictional_universal_presenter")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sgo_programs(request):
    school = actor_scope(request, ("parent",))
    grants = family_grants(request.user).filter(school_key=school.pk)
    result = []
    for grant in grants:
        program_scope(request, grant.program_id)
        existing = SGOFamilyIntake.objects.filter(grant=grant).first()
        result.append({"id": str(grant.program_id), "organization_id": str(grant.program.organization_id),
            "organization": grant.program.organization.legal_name, "name": grant.program.name,
            "calendar_year": grant.program.calendar_year, "policy_version": grant.program.eligibility_rule_version,
            "consent_version": grant.consent_version, "application_id": str(existing.application_id) if existing else None})
    return private({"programs": result, "synthetic_only": True, "funds_status": "NONCASH_ONLY"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sgo_submit(request):
    actor_scope(request, ("parent",))
    data = _payload(request, {"program_id", "grade_level", "consent", "consent_version", "submission_key"})
    program = _program_id(data.get("program_id"))
    program_scope(request, program)
    intake, created = submit_family_application(user=request.user, program_id=program,
        grade_level=data.get("grade_level"), consent=data.get("consent"), consent_version=data.get("consent_version"),
        submission_key=data.get("submission_key"))
    response = private({"application": serialize_intake(intake), "created": created})
    response.status_code = 201 if created else 200
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sgo_application(request, application_id):
    actor_scope(request, ("parent",))
    application_scope(request, application_id)
    return private({"application": serialize_intake(get_family_application(user=request.user, application_id=application_id))})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sgo_correct(request, application_id):
    actor_scope(request, ("parent",))
    application_scope(request, application_id)
    data = _payload(request, {"expected_revision", "grade_level", "correction_key"})
    intake, changed = correct_family_application(user=request.user, application_id=application_id,
        expected_revision=data.get("expected_revision"), grade_level=data.get("grade_level"), correction_key=data.get("correction_key"))
    return private({"application": serialize_intake(intake), "changed": changed})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sgo_processor_programs(request):
    school = actor_scope(request, ("finance_director",))
    result = []
    for item in processor_programs(request.user):
        if SGOFamilyGrant.objects.filter(program=item.program, school_key=school.pk).exists():
            program_scope(request, item.program_id, processor=True)
            result.append({"id": str(item.program_id), "name": item.program.name,
                "organization": item.program.organization.legal_name, "organization_id": str(item.program.organization_id)})
    return private({"programs": result, "authority": "PROCESSOR_VERIFICATION_ONLY", "funds_status": "NONCASH_ONLY"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sgo_queue(request, program_id):
    program_scope(request, program_id, processor=True)
    rows = processor_queue(user=request.user, program_id=program_id)
    return private({"applications": [serialize_intake(row, authority="PROCESSOR_VERIFICATION_ONLY") for row in rows],
        "program_id": str(program_id), "authority": "PROCESSOR_VERIFICATION_ONLY", "funds_status": "NONCASH_ONLY"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sgo_request_correction(request, application_id):
    actor_scope(request, ("finance_director",))
    application_scope(request, application_id, processor=True)
    data = _payload(request, {"expected_revision", "reason", "request_key"})
    intake, changed = request_processor_correction(user=request.user, application_id=application_id,
        expected_revision=data.get("expected_revision"), reason=data.get("reason"), request_key=data.get("request_key"))
    return private({"application": serialize_intake(intake, authority="PROCESSOR_VERIFICATION_ONLY"), "changed": changed})
