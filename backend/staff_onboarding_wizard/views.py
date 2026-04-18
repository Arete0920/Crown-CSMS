"""
staff_onboarding_wizard/views.py

5 endpoints for the Staff Onboarding Wizard:

  POST /api/v1/staff-onboarding-wizard/sessions/                → create_session
  POST /api/v1/staff-onboarding-wizard/sessions/<id>/configure/ → configure_session
  GET  /api/v1/staff-onboarding-wizard/sessions/<id>/preview/   → preview_session
  POST /api/v1/staff-onboarding-wizard/sessions/<id>/commit/    → commit_session
  GET  /api/v1/staff-onboarding-wizard/sessions/<id>/verify/    → verify_session

All endpoints:
  - Require authentication (JWT or Session)
  - Are tenant-scoped via X-School-Id header → get_request_school_id()
  - Enforce school isolation: session lookups include school_id
"""

import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from audit.models import AuditLog
from core.models import School, Staff
from households.scoping import get_request_school_id

from .models import StaffOnboardingWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)

# Single source of truth — mirrors core.Staff.ROLE_CHOICES exactly.
VALID_ROLES = {c[0] for c in Staff.ROLE_CHOICES}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(
        StaffOnboardingWizardSession, id=session_id, school_id=school_id
    )


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)
    session = StaffOnboardingWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure — collect staff details
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    first_name = (request.data.get("first_name") or "").strip()
    last_name  = (request.data.get("last_name")  or "").strip()
    email      = (request.data.get("email")      or "").strip()
    role_type  = (request.data.get("role_type")  or "").strip()

    errors = []
    if not first_name:
        errors.append("first_name is required")
    if not last_name:
        errors.append("last_name is required")
    if not email:
        errors.append("email is required")
    if not role_type:
        errors.append("role_type is required")
    elif role_type not in VALID_ROLES:
        errors.append(f"role_type must be one of: {sorted(VALID_ROLES)}")

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.first_name = first_name
    session.last_name  = last_name
    session.email      = email
    session.role_type  = role_type
    session.status     = StaffOnboardingWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({"session_id": str(session.id), "status": session.status})


# ---------------------------------------------------------------------------
# 3. Preview — show what will be created (read-only)
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def preview_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == StaffOnboardingWizardSession.STATUS_DRAFT:
        return Response(
            {"error": "Session must be configured before preview"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    duplicate = Staff.objects.filter(
        school_id=school_id, email=session.email
    ).exists()

    session.status = StaffOnboardingWizardSession.STATUS_PREVIEWED
    session.save(update_fields=["status", "updated_at"])

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "preview": {
            "first_name": session.first_name,
            "last_name":  session.last_name,
            "email":      session.email,
            "role_type":  session.role_type,
            "school_id":  str(session.school_id),
        },
        "warnings": (
            [f"A staff record with email {session.email!r} already exists in this school."]
            if duplicate else []
        ),
    })


# ---------------------------------------------------------------------------
# 4. Commit — create the Staff record
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        StaffOnboardingWizardSession.STATUS_CONFIGURED,
        StaffOnboardingWizardSession.STATUS_PREVIEWED,
    ):
        return Response(
            {"error": "Session must be configured or previewed before commit"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        staff, created = Staff.objects.get_or_create(
            school_id=school_id,
            email=session.email,
            defaults={
                "first_name": session.first_name,
                "last_name":  session.last_name,
                "role_type":  session.role_type,
                "status":     "ACTIVE",
            },
        )

        result = {
            "staff_id":  str(staff.id),
            "email":     staff.email,
            "role_type": staff.role_type,
            "created":   created,
            "message":   (
                "Staff member created."
                if created
                else "Staff already existed; linked to existing record."
            ),
        }
        session.commit_result = result
        session.status        = StaffOnboardingWizardSession.STATUS_COMMITTED
        session.save()

    # Audit log — non-fatal if it fails
    try:
        AuditLog.objects.create(
            user_id=getattr(request.user, "id", None),
            action="staff_onboarding.commit",
            model="Staff",
            object_id=result["staff_id"],
            metadata={
                "email":     result["email"],
                "role_type": result["role_type"],
                "created":   result["created"],
                "school_id": str(school_id),
                "session_id": str(session.id),
            },
        )
    except Exception as exc:
        logger.warning("staff_onboarding.commit audit log skipped: %s", exc)

    return Response({"session_id": str(session.id), "status": session.status, "result": result})


# ---------------------------------------------------------------------------
# 5. Verify — confirm the Staff record exists
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != StaffOnboardingWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": "Session must be committed before verify"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    staff_exists = Staff.objects.filter(
        school_id=school_id, email=session.email
    ).exists()

    session.status = StaffOnboardingWizardSession.STATUS_VERIFIED
    session.save(update_fields=["status", "updated_at"])

    return Response({
        "session_id":   str(session.id),
        "status":       session.status,
        "staff_exists": staff_exists,
        "email":        session.email,
    })
