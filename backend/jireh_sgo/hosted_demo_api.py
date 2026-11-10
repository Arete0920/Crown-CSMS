"""Hosted SGO processor-demo APIs, distinct from local-only SGO endpoints.

Programs and their fictional partner organizations are bound to one buyer
workspace. A buyer school role is never an SGO grant or processor assignment.
CROWN only processes partner applications: no scholarship award/fund actions.
"""
from __future__ import annotations

from django.db.models import F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from core.models import Student
from sandbox_demo.hosted_jireh import (
    demo_aid_family, demo_program, demo_student_ids, require_hosted_workspace,
)
from .family_intake import (
    correct_family_application, family_grants, get_family_application,
    processor_programs, processor_queue, request_processor_correction,
    serialize_intake, submit_family_application,
)
from .models import SGOFamilyGrant, SGOFamilyIntake, SGOProcessorAssignment
from .read_only_api import private


def _payload(data, permitted):
    if not isinstance(data, dict) or set(data) - permitted:
        raise ValidationError({"detail": "Only fixed fictional application fields are accepted."})
    return data


def _family_program(workspace, user, raw_program):
    # Both an independently bound synthetic partner/program and an individual
    # applicant grant are mandatory; school membership alone is insufficient.
    demo_aid_family(workspace, user)
    program = demo_program(workspace, raw_program)
    authorized_students = demo_student_ids(workspace)
    grant = SGOFamilyGrant.objects.filter(
        user=user, program=program, active=True,
        school_key=workspace.school_id,
        student_key__in=authorized_students,
    ).first()
    if grant is None:
        raise NotFound("Not found.")
    return program, grant


def _verified_intake(workspace, user, application_id):
    intake = get_family_application(user=user, application_id=application_id)
    program, grant = _family_program(workspace, user, intake.application.program_id)
    if (
        intake.grant_id != grant.id
        or intake.application.school_key != workspace.school_id
        or intake.application.student_key != grant.student_key
        or intake.application.program_id != program.id
    ):
        raise NotFound("Not found.")
    return intake


def _processor_program(workspace, user, program_id):
    program = demo_program(workspace, program_id)
    if not SGOProcessorAssignment.objects.filter(
        user=user, program=program, active=True,
    ).exists():
        raise NotFound("Not found.")
    return program


def _processor_intake(workspace, user, application_id):
    intake = SGOFamilyIntake.objects.select_related(
        "application__program__organization", "grant"
    ).filter(
        application_id=application_id, grant__active=True, grant__school_key=workspace.school_id,
        grant__student_key__in=demo_student_ids(workspace),
    ).first()
    if intake is None:
        raise NotFound("Not found.")
    _processor_program(workspace, user, intake.application.program_id)
    if (
        intake.application.school_key != workspace.school_id
        or intake.application.student_key != intake.grant.student_key
    ):
        raise NotFound("Not found.")
    return intake


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hosted_family_programs(request):
    workspace, _ = require_hosted_workspace(request, ("parent",))
    demo_aid_family(workspace, request.user)
    authorized_students = demo_student_ids(workspace)
    grants = family_grants(request.user).filter(
        school_key=workspace.school_id, student_key__in=authorized_students,
        program__sandbox_buyer_program__partner__workspace=workspace,
        program__sandbox_buyer_program__partner__organization_id=F("program__organization_id"),
    )
    active = dict(SGOFamilyIntake.objects.filter(
        grant_id__in=grants.values("id")
    ).values_list("grant_id", "application_id"))
    return private({
        "synthetic_only": True, "funds_status": "NONCASH_ONLY",
        "programs": [{
            "id": str(grant.program_id),
            "organization_id": str(grant.program.organization_id),
            "organization": grant.program.organization.legal_name,
            "name": grant.program.name,
            "policy_version": grant.program.eligibility_rule_version,
            "consent_version": grant.consent_version,
            "application_id": str(active[grant.pk]) if grant.pk in active else None,
        } for grant in grants],
    })


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hosted_family_submit(request):
    workspace, _ = require_hosted_workspace(request, ("parent",))
    data = _payload(request.data, {
        "program_id", "grade_level", "consent", "consent_version", "submission_key",
    })
    program, _ = _family_program(workspace, request.user, data.get("program_id"))
    intake, created = submit_family_application(
        user=request.user, program_id=program.id,
        grade_level=data.get("grade_level"), consent=data.get("consent"),
        consent_version=data.get("consent_version"),
        submission_key=data.get("submission_key"),
    )
    response = private({
        "synthetic_only": True, "created": created,
        "application": serialize_intake(intake),
    })
    response.status_code = 201 if created else 200
    return response


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hosted_family_application(request, application_id):
    workspace, _ = require_hosted_workspace(request, ("parent",))
    return private({
        "synthetic_only": True,
        "application": serialize_intake(_verified_intake(workspace, request.user, application_id)),
    })


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hosted_family_correct(request, application_id):
    workspace, _ = require_hosted_workspace(request, ("parent",))
    _verified_intake(workspace, request.user, application_id)
    data = _payload(request.data, {"expected_revision", "grade_level", "correction_key"})
    intake, changed = correct_family_application(
        user=request.user, application_id=application_id,
        expected_revision=data.get("expected_revision"),
        grade_level=data.get("grade_level"),
        correction_key=data.get("correction_key"),
    )
    return private({
        "synthetic_only": True, "changed": changed,
        "application": serialize_intake(intake),
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hosted_processor_programs(request):
    workspace, _ = require_hosted_workspace(
        request, ("finance_director", "school_admin"),
    )
    assignments = processor_programs(request.user).filter(
        program__sandbox_buyer_program__partner__workspace=workspace,
        program__sandbox_buyer_program__partner__organization_id=F("program__organization_id"),
    )
    return private({
        "synthetic_only": True, "authority": "PROCESSOR_VERIFICATION_ONLY",
        "funds_status": "NONCASH_ONLY",
        "programs": [{
            "id": str(item.program_id), "name": item.program.name,
            "organization_id": str(item.program.organization_id),
            "organization": item.program.organization.legal_name,
        } for item in assignments],
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hosted_processor_queue(request, program_id):
    workspace, _ = require_hosted_workspace(
        request, ("finance_director", "school_admin"),
    )
    program = _processor_program(workspace, request.user, program_id)
    rows = processor_queue(user=request.user, program_id=program.pk).filter(
        grant__school_key=workspace.school_id, grant__active=True,
        grant__student_key__in=demo_student_ids(workspace),
        application__school_key=workspace.school_id,
    )
    return private({
        "synthetic_only": True, "authority": "PROCESSOR_VERIFICATION_ONLY",
        "funds_status": "NONCASH_ONLY", "program_id": str(program.pk),
        "applications": [
            serialize_intake(row, authority="PROCESSOR_VERIFICATION_ONLY")
            for row in rows
        ],
    })


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hosted_processor_request_correction(request, application_id):
    workspace, _ = require_hosted_workspace(
        request, ("finance_director", "school_admin"),
    )
    _processor_intake(workspace, request.user, application_id)
    data = _payload(request.data, {"expected_revision", "reason", "request_key"})
    intake, changed = request_processor_correction(
        user=request.user, application_id=application_id,
        expected_revision=data.get("expected_revision"),
        reason=data.get("reason"), request_key=data.get("request_key"),
    )
    return private({
        "synthetic_only": True, "authority": "PROCESSOR_VERIFICATION_ONLY",
        "funds_status": "NONCASH_ONLY", "changed": changed,
        "application": serialize_intake(intake, authority="PROCESSOR_VERIFICATION_ONLY"),
    })
