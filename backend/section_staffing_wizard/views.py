"""
section_staffing_wizard/views.py

Steps:
  POST   /sessions/                              → create_session
  POST   /sessions/<uuid>/configure/             → configure_session  (academic_year_id + term)
  POST   /sessions/<uuid>/load_sections/         → load_sections      (sections_pool)
  POST   /sessions/<uuid>/stage_assignments/     → stage_assignments  (assignments)
  POST   /sessions/<uuid>/commit/                → commit_session
  GET    /sessions/<uuid>/verify/                → verify_session
"""
import uuid as _uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id

from .models import SectionStaffingWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_ROLES = {"primary", "aide", "co-teacher"}


def _get_session(session_id, school_id):
    return get_object_or_404(SectionStaffingWizardSession, id=session_id, school__id=school_id)


def _parse_uuid(value, field_name):
    try:
        return _uuid.UUID(str(value)), None
    except (ValueError, AttributeError):
        return None, f"{field_name} must be a valid UUID"


# ---------------------------------------------------------------------------
# Step 1: Create session
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = SectionStaffingWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Step 2: Configure (academic year + term)
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == SectionStaffingWizardSession.STATUS_COMMITTED:
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

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


# ---------------------------------------------------------------------------
# Step 3: Load sections pool
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def load_sections(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != SectionStaffingWizardSession.STATUS_CONFIGURED:
        return Response(
            {"error": f"Session must be in 'configured' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sections_pool = request.data.get("sections_pool")
    if not isinstance(sections_pool, list) or len(sections_pool) == 0:
        return Response({"error": "sections_pool must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    for i, sec in enumerate(sections_pool):
        if not sec.get("section_id"):
            return Response({"error": f"sections_pool[{i}].section_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.sections_pool = sections_pool
    session.status = SectionStaffingWizardSession.STATUS_SECTIONS_LOADED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "section_count": len(sections_pool),
    })


# ---------------------------------------------------------------------------
# Step 4: Stage assignments
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_assignments(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != SectionStaffingWizardSession.STATUS_SECTIONS_LOADED:
        return Response(
            {"error": f"Session must be in 'sections_loaded' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    assignments = request.data.get("assignments")
    if not isinstance(assignments, list) or len(assignments) == 0:
        return Response({"error": "assignments must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    pool_ids = {str(s["section_id"]) for s in session.sections_pool}
    errors = []
    for i, a in enumerate(assignments):
        if not a.get("section_id"):
            errors.append(f"assignments[{i}].section_id is required")
        elif str(a["section_id"]) not in pool_ids:
            errors.append(f"assignments[{i}].section_id not in loaded sections pool")
        if not a.get("teacher_id"):
            errors.append(f"assignments[{i}].teacher_id is required")
        role = a.get("role", "primary")
        if role not in VALID_ROLES:
            errors.append(f"assignments[{i}].role must be one of {sorted(VALID_ROLES)}")

    if errors:
        return Response({"error": errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    session.assignments = assignments
    session.status = SectionStaffingWizardSession.STATUS_ASSIGNMENTS_STAGED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "assignment_count": len(assignments),
    })


# ---------------------------------------------------------------------------
# Step 5: Commit
# ---------------------------------------------------------------------------

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
        return Response(
            {"error": f"Session must be in 'assignments_staged' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    from academics.models import SectionTeacher

    assigned = 0
    errors = []

    with transaction.atomic():
        for a in session.assignments:
            try:
                SectionTeacher.objects.update_or_create(
                    section_id=a["section_id"],
                    teacher_id=a["teacher_id"],
                    defaults={"role": a.get("role", "primary"), "school_id": school_id},
                )
                assigned += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        result = {"assigned": assigned, "errors": errors}
        session.commit_result = result
        session.status = SectionStaffingWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **result})


# ---------------------------------------------------------------------------
# Step 6: Verify
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        SectionStaffingWizardSession.STATUS_COMMITTED,
        SectionStaffingWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Session must be committed before verify (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.status == SectionStaffingWizardSession.STATUS_COMMITTED:
        session.status = SectionStaffingWizardSession.STATUS_VERIFIED
        session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **(session.commit_result or {}),
    })
