from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id
from core.models import School
from room_setup_wizard.models import Room, RoomSetupWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(RoomSetupWizardSession, id=session_id, school__id=school_id)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)
    sess = RoomSetupWizardSession.objects.create(school=school)
    return Response({"session_id": str(sess.id), "status": sess.status}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "draft":
        return Response({"error": "Session not in draft state"}, status=status.HTTP_400_BAD_REQUEST)

    rooms = request.data.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        return Response({"error": "rooms must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    normalized = []
    for i, row in enumerate(rooms):
        if not isinstance(row, dict):
            return Response({"error": f"rooms[{i}] must be an object"}, status=status.HTTP_400_BAD_REQUEST)
        code = str(row.get("code", "")).strip().upper()
        if not code:
            return Response({"error": f"rooms[{i}].code required"}, status=status.HTTP_400_BAD_REQUEST)
        cap = int(row.get("capacity", 0))
        if cap < 0:
            return Response({"error": f"rooms[{i}].capacity must be >= 0"}, status=status.HTTP_400_BAD_REQUEST)
        normalized.append({
            "code": code,
            "name": str(row.get("name", "")).strip(),
            "capacity": cap,
        })

    sess.rooms = normalized
    sess.status = "configured"
    sess.save(update_fields=["rooms", "status"])
    return Response({"status": sess.status, "count": len(normalized)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "configured":
        return Response({"error": "Commit requires configured state"}, status=status.HTTP_400_BAD_REQUEST)

    created = 0
    updated = 0
    with transaction.atomic():
        for row in sess.rooms or []:
            _, was_created = Room.objects.update_or_create(
                school_id=sess.school_id,
                code=row["code"],
                defaults={"name": row.get("name", ""), "capacity": row.get("capacity", 0), "is_active": True},
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        sess.commit_result = {"created": created, "updated": updated, "total": len(sess.rooms or [])}
        sess.status = "committed"
        sess.save(update_fields=["commit_result", "status"])

    return Response({"status": sess.status, **sess.commit_result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status not in ("committed", "verified"):
        return Response({"error": "Verify requires committed state"}, status=status.HTTP_400_BAD_REQUEST)

    rooms = list(
        Room.objects.filter(school_id=sess.school_id, is_active=True)
        .values("id", "code", "name", "capacity")
        .order_by("code")
    )
    sess.status = "verified"
    sess.save(update_fields=["status"])
    return Response({"status": sess.status, "rooms": rooms, "count": len(rooms)})
