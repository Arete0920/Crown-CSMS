import uuid as _uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import AssignmentCategory, Section
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
    except (ValueError, AttributeError, TypeError):
        return None, f"{field_name} must be a valid UUID"


def _section_for_session(session, school_id):
    if not session.gradebook_id:
        return None
    return Section.objects.filter(pk=session.gradebook_id, school_id=school_id).first()


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = GradeWeightsWizardSession.objects.create(school=school, created_by=request.user)
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status in (GradeWeightsWizardSession.STATUS_COMMITTED, GradeWeightsWizardSession.STATUS_VERIFIED):
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

    section_raw = request.data.get("section_id") or request.data.get("gradebook_id")
    if section_raw:
        section_id, error = _parse_uuid(section_raw, "section_id")
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        if not Section.objects.filter(pk=section_id, school_id=school_id).exists():
            return Response({"error": "section_id was not found for this school"}, status=status.HTTP_400_BAD_REQUEST)
        session.gradebook_id = section_id

    marking_period = str(request.data.get("marking_period", "")).strip()
    if not marking_period:
        return Response({"error": "marking_period is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.marking_period = marking_period
    session.status = GradeWeightsWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "section_id": str(session.gradebook_id) if session.gradebook_id else None,
        "gradebook_id": str(session.gradebook_id) if session.gradebook_id else None,
        "marking_period": session.marking_period,
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_categories(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status != GradeWeightsWizardSession.STATUS_CONFIGURED:
        return Response({"error": f"Session must be in 'configured' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)

    categories = request.data.get("categories_staged")
    if not isinstance(categories, list) or not categories:
        return Response({"error": "categories_staged must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    names = set()
    total_weight = Decimal("0")
    normalized = []
    for index, category in enumerate(categories):
        name = str(category.get("name") or "").strip()
        if not name:
            return Response({"error": f"categories_staged[{index}].name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if name.casefold() in names:
            return Response({"error": f"categories_staged[{index}].name must be unique"}, status=status.HTTP_400_BAD_REQUEST)
        names.add(name.casefold())
        try:
            weight = Decimal(str(category.get("weight_pct")))
        except Exception:
            return Response({"error": f"categories_staged[{index}].weight_pct must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)
        if weight <= 0:
            return Response({"error": f"categories_staged[{index}].weight_pct must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)
        total_weight += weight
        normalized.append({"name": name, "weight_pct": float(weight)})

    if total_weight != Decimal("100"):
        return Response({"error": f"weight_pct values must sum to 100 (got {total_weight})"}, status=status.HTTP_400_BAD_REQUEST)

    session.categories_staged = normalized
    session.status = GradeWeightsWizardSession.STATUS_CATEGORIES_STAGED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "category_count": len(normalized),
        "total_weight_pct": float(total_weight),
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status in (GradeWeightsWizardSession.STATUS_COMMITTED, GradeWeightsWizardSession.STATUS_VERIFIED):
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
    if session.status != GradeWeightsWizardSession.STATUS_CATEGORIES_STAGED:
        return Response({"error": f"Session must be in 'categories_staged' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    section = _section_for_session(session, school_id)
    if section is None:
        return Response({"error": "A valid section_id is required before commit"}, status=status.HTTP_400_BAD_REQUEST)

    created = 0
    updated = 0
    staged_names = [category["name"] for category in session.categories_staged]
    with transaction.atomic():
        deactivated = AssignmentCategory.objects.filter(
            school_id=school_id,
            section=section,
            is_active=True,
        ).exclude(name__in=staged_names).update(is_active=False)

        for index, category in enumerate(session.categories_staged):
            _, was_created = AssignmentCategory.objects.update_or_create(
                school_id=school_id,
                section=section,
                name=category["name"],
                defaults={
                    "weight_percent": Decimal(str(category["weight_pct"])),
                    "sort_order": index,
                    "is_active": True,
                },
            )
            created += int(was_created)
            updated += int(not was_created)

    active = AssignmentCategory.objects.filter(school_id=school_id, section=section, is_active=True)
    active_count = active.count()
    total_weight = active.aggregate(total=Sum("weight_percent"))["total"] or Decimal("0")
    result = {
        "section_id": str(section.id),
        "marking_period": session.marking_period,
        "created": created,
        "updated": updated,
        "deactivated": deactivated,
        "active_count": active_count,
        "total_weight_pct": float(total_weight),
        "errors": [],
    }
    session.commit_result = result
    session.status = GradeWeightsWizardSession.STATUS_COMMITTED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, **result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status not in (GradeWeightsWizardSession.STATUS_COMMITTED, GradeWeightsWizardSession.STATUS_VERIFIED):
        return Response({"error": f"Session must be committed before verify (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    section = _section_for_session(session, school_id)
    if section is None:
        return Response({"error": "Configured section no longer exists"}, status=status.HTTP_409_CONFLICT)

    active = AssignmentCategory.objects.filter(school_id=school_id, section=section, is_active=True)
    total_weight = active.aggregate(total=Sum("weight_percent"))["total"] or Decimal("0")
    if total_weight != Decimal("100"):
        return Response({"error": f"Active category weights total {total_weight}, expected 100"}, status=status.HTTP_409_CONFLICT)

    if session.status == GradeWeightsWizardSession.STATUS_COMMITTED:
        session.status = GradeWeightsWizardSession.STATUS_VERIFIED
        session.save()
    result = {
        **(session.commit_result or {}),
        "section_id": str(section.id),
        "active_count": active.count(),
        "total_weight_pct": float(total_weight),
    }
    return Response({"session_id": str(session.id), "status": session.status, **result})
