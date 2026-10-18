"""Section staffing wizard backed by canonical academics Section/TeacherAssignment records."""
import uuid as _uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from households.scoping import get_request_school_id
from .models import SectionStaffingWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

# TeacherAssignment currently represents section/staff membership without a role column.
# Fail closed instead of silently discarding aide/co-teacher semantics.
VALID_ROLES = {"primary"}


def _get_session(session_id, school_id):
    return get_object_or_404(SectionStaffingWizardSession, id=session_id, school__id=school_id)


def _parse_uuid(value, field_name):
    try:
        return _uuid.UUID(str(value)), None
    except (ValueError, AttributeError):
        return None, f"{field_name} must be a valid UUID"


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = SectionStaffingWizardSession.objects.create(school=school, created_by=request.user)
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status in (
        SectionStaffingWizardSession.STATUS_COMMITTED,
        SectionStaffingWizardSession.STATUS_VERIFIED,
    ):
        return Response({"error": "Committed or verified sessions are immutable"}, status=status.HTTP_400_BAD_REQUEST)

    ay_raw = request.data.get("academic_year_id")
    term = str(request.data.get("term", "")).strip()
    if ay_raw:
        ay_uuid, err = _parse_uuid(ay_raw, "academic_year_id")
        if err:
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)
        session.academic_year_id = ay_uuid
    session.term = term
    session.status = SectionStaffingWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "academic_year_id": str(session.academic_year_id) if session.academic_year_id else None,
        "term": session.term,
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def load_sections(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status != SectionStaffingWizardSession.STATUS_CONFIGURED:
        return Response({"error": f"Session must be in 'configured' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)

    sections_pool = request.data.get("sections_pool")
    if not isinstance(sections_pool, list) or not sections_pool:
        return Response({"error": "sections_pool must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
    for i, sec in enumerate(sections_pool):
        if not sec.get("section_id"):
            return Response({"error": f"sections_pool[{i}].section_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.sections_pool = sections_pool
    session.status = SectionStaffingWizardSession.STATUS_SECTIONS_LOADED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "section_count": len(sections_pool)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_assignments(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status != SectionStaffingWizardSession.STATUS_SECTIONS_LOADED:
        return Response({"error": f"Session must be in 'sections_loaded' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)

    assignments = request.data.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        return Response({"error": "assignments must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    pool_ids = {str(s["section_id"]) for s in session.sections_pool}
    errors = []
    for i, assignment in enumerate(assignments):
        if not assignment.get("section_id"):
            errors.append(f"assignments[{i}].section_id is required")
        elif str(assignment["section_id"]) not in pool_ids:
            errors.append(f"assignments[{i}].section_id not in loaded sections pool")
        if not assignment.get("teacher_id"):
            errors.append(f"assignments[{i}].teacher_id is required")
        role = assignment.get("role", "primary")
        if role not in VALID_ROLES:
            errors.append("assignments[%d].role must be 'primary' until canonical staffing roles are modeled" % i)
    if errors:
        return Response({"error": errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    session.assignments = assignments
    session.status = SectionStaffingWizardSession.STATUS_ASSIGNMENTS_STAGED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "assignment_count": len(assignments)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status == SectionStaffingWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
    if session.status != SectionStaffingWizardSession.STATUS_ASSIGNMENTS_STAGED:
        return Response({"error": f"Session must be in 'assignments_staged' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    from academics.models import Section, TeacherAssignment
    from core.models import Staff

    # Validate the complete batch before writing anything. This prevents a partially
    # committed staffing session and enforces tenant ownership at the canonical records.
    resolved = []
    for i, assignment in enumerate(session.assignments):
        section = Section.objects.filter(id=assignment["section_id"], school_id=school_id).first()
        if section is None:
            return Response({"error": f"assignments[{i}].section_id is not a canonical section for this school"}, status=status.HTTP_400_BAD_REQUEST)
        staff = Staff.objects.filter(id=assignment["teacher_id"], school_id=school_id, status="ACTIVE").first()
        if staff is None:
            return Response({"error": f"assignments[{i}].teacher_id is not active staff for this school"}, status=status.HTTP_400_BAD_REQUEST)
        resolved.append((section, staff))

    with transaction.atomic():
        assigned = 0
        for section, staff in resolved:
            _, created = TeacherAssignment.objects.get_or_create(
                school_id=school_id,
                section=section,
                staff=staff,
            )
            if created:
                assigned += 1
        result = {"assigned": assigned, "requested": len(resolved), "errors": []}
        session.commit_result = result
        session.status = SectionStaffingWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status not in (SectionStaffingWizardSession.STATUS_COMMITTED, SectionStaffingWizardSession.STATUS_VERIFIED):
        return Response({"error": f"Session must be committed before verify (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    if session.status == SectionStaffingWizardSession.STATUS_COMMITTED:
        session.status = SectionStaffingWizardSession.STATUS_VERIFIED
        session.save()
    return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
