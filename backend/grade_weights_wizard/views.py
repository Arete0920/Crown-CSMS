"""
grade_weights_wizard/views.py

Steps:
  POST   /sessions/                              → create_session
  POST   /sessions/<uuid>/configure/             → configure_session   (gradebook_id + marking_period)
  POST   /sessions/<uuid>/stage_categories/      → stage_categories    (categories_staged)
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

from .models import GradeWeightsWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(GradeWeightsWizardSession, id=session_id, school__id=school_id)


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
    session = GradeWeightsWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Step 2: Configure (gradebook + marking period)
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == GradeWeightsWizardSession.STATUS_COMMITTED:
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

    gb_raw = request.data.get("gradebook_id")
    if gb_raw:
        gb_uuid, err = _parse_uuid(gb_raw, "gradebook_id")
        if err:
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)
        session.gradebook_id = gb_uuid

    marking_period = str(request.data.get("marking_period", "")).strip()
    if not marking_period:
        return Response({"error": "marking_period is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.marking_period = marking_period
    session.status = GradeWeightsWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "gradebook_id": str(session.gradebook_id) if session.gradebook_id else None,
        "marking_period": session.marking_period,
    })


# ---------------------------------------------------------------------------
# Step 3: Stage categories
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_categories(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != GradeWeightsWizardSession.STATUS_CONFIGURED:
        return Response(
            {"error": f"Session must be in 'configured' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    categories_staged = request.data.get("categories_staged")
    if not isinstance(categories_staged, list) or len(categories_staged) == 0:
        return Response({"error": "categories_staged must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    total_weight = 0
    for i, cat in enumerate(categories_staged):
        if not cat.get("name"):
            return Response({"error": f"categories_staged[{i}].name is required"}, status=status.HTTP_400_BAD_REQUEST)
        weight = cat.get("weight_pct")
        if not isinstance(weight, (int, float)) or weight <= 0:
            return Response(
                {"error": f"categories_staged[{i}].weight_pct must be a positive number"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total_weight += weight

    if round(total_weight) != 100:
        return Response(
            {"error": f"weight_pct values must sum to 100 (got {total_weight})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.categories_staged = categories_staged
    session.status = GradeWeightsWizardSession.STATUS_CATEGORIES_STAGED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "category_count": len(categories_staged),
        "total_weight_pct": total_weight,
    })


# ---------------------------------------------------------------------------
# Step 4: Commit
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == GradeWeightsWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})

    if session.status != GradeWeightsWizardSession.STATUS_CATEGORIES_STAGED:
        return Response(
            {"error": f"Session must be in 'categories_staged' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    from academics.models import GradeCategory

    created = 0
    updated = 0
    errors = []

    with transaction.atomic():
        for cat in session.categories_staged:
            try:
                defaults = {
                    "weight_pct": cat.get("weight_pct", 0),
                    "drop_lowest": int(cat.get("drop_lowest", 0)),
                    "description": cat.get("description", ""),
                }
                filter_kwargs = {
                    "school_id": school_id,
                    "name": cat["name"],
                    "marking_period": session.marking_period,
                }
                if session.gradebook_id:
                    filter_kwargs["gradebook_id"] = session.gradebook_id

                _, was_created = GradeCategory.objects.update_or_create(
                    **filter_kwargs,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        result = {"created": created, "updated": updated, "errors": errors}
        session.commit_result = result
        session.status = GradeWeightsWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **result})


# ---------------------------------------------------------------------------
# Step 5: Verify
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        GradeWeightsWizardSession.STATUS_COMMITTED,
        GradeWeightsWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Session must be committed before verify (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.status == GradeWeightsWizardSession.STATUS_COMMITTED:
        session.status = GradeWeightsWizardSession.STATUS_VERIFIED
        session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **(session.commit_result or {}),
    })
