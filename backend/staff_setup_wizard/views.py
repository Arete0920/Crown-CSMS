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
from staff_setup_wizard.models import StaffMember, StaffSetupWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(StaffSetupWizardSession, id=session_id, school__id=school_id)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)
    sess = StaffSetupWizardSession.objects.create(school=school)
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

    roster = request.data.get("roster")
    if not isinstance(roster, list) or not roster:
        return Response({"error": "roster must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    normalized = []
    for i, row in enumerate(roster):
        if not isinstance(row, dict):
            return Response({"error": f"roster[{i}] must be an object"}, status=status.HTTP_400_BAD_REQUEST)
        email = str(row.get("email", "")).strip().lower()
        if not email:
            return Response({"error": f"roster[{i}].email required"}, status=status.HTTP_400_BAD_REQUEST)
        normalized.append({
            "email": email,
            "first_name": str(row.get("first_name", "")).strip(),
            "last_name": str(row.get("last_name", "")).strip(),
            "is_teacher": bool(row.get("is_teacher", False)),
            "is_admin": bool(row.get("is_admin", False)),
            "is_active": bool(row.get("is_active", True)),
        })

    sess.roster = normalized
    sess.status = "configured"
    sess.save(update_fields=["roster", "status"])
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
        for row in sess.roster or []:
            _, was_created = StaffMember.objects.update_or_create(
                school_id=sess.school_id,
                email=row["email"],
                defaults={
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "is_teacher": bool(row.get("is_teacher", False)),
                    "is_admin": bool(row.get("is_admin", False)),
                    "is_active": bool(row.get("is_active", True)),
                },
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        sess.commit_result = {"created": created, "updated": updated, "total": len(sess.roster or [])}
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

    staff = list(
        StaffMember.objects.filter(school_id=sess.school_id, is_active=True)
        .values("id", "email", "first_name", "last_name", "is_teacher", "is_admin")
        .order_by("email")
    )
    sess.status = "verified"
    sess.save(update_fields=["status"])
    return Response({"status": sess.status, "staff": staff, "count": len(staff)})
