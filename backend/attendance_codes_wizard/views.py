"""
attendance_codes_wizard/views.py

Steps:
  POST   /sessions/                             → create_session
  POST   /sessions/<uuid>/configure/            → configure_session   (policy_config)
  POST   /sessions/<uuid>/stage_codes/          → stage_codes         (codes_staged)
  POST   /sessions/<uuid>/commit/               → commit_session
  GET    /sessions/<uuid>/verify/               → verify_session
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id

from .models import AttendanceCodesWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

REQUIRED_CODE_FIELDS = {"code", "label"}


def _get_session(session_id, school_id):
    return get_object_or_404(AttendanceCodesWizardSession, id=session_id, school__id=school_id)


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
    session = AttendanceCodesWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Step 2: Configure policy
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == AttendanceCodesWizardSession.STATUS_COMMITTED:
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

    policy_config = request.data.get("policy_config")
    if not isinstance(policy_config, dict):
        return Response({"error": "policy_config must be an object"}, status=status.HTTP_400_BAD_REQUEST)

    session.policy_config = policy_config
    session.status = AttendanceCodesWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({"session_id": str(session.id), "status": session.status})


# ---------------------------------------------------------------------------
# Step 3: Stage codes
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_codes(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != AttendanceCodesWizardSession.STATUS_CONFIGURED:
        return Response(
            {"error": f"Session must be in 'configured' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    codes_staged = request.data.get("codes_staged")
    if not isinstance(codes_staged, list) or len(codes_staged) == 0:
        return Response({"error": "codes_staged must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    seen_codes = set()
    for i, c in enumerate(codes_staged):
        missing = REQUIRED_CODE_FIELDS - set(c.keys())
        if missing:
            return Response(
                {"error": f"codes_staged[{i}] missing fields: {sorted(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        code_val = str(c["code"]).strip().upper()
        if not code_val:
            return Response({"error": f"codes_staged[{i}].code must not be empty"}, status=status.HTTP_400_BAD_REQUEST)
        if code_val in seen_codes:
            return Response({"error": f"Duplicate code: '{code_val}'"}, status=status.HTTP_400_BAD_REQUEST)
        seen_codes.add(code_val)

    session.codes_staged = codes_staged
    session.status = AttendanceCodesWizardSession.STATUS_CODES_STAGED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "code_count": len(codes_staged),
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

    if session.status == AttendanceCodesWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})

    if session.status != AttendanceCodesWizardSession.STATUS_CODES_STAGED:
        return Response(
            {"error": f"Session must be in 'codes_staged' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    from attendance.models import AttendanceCode

    created = 0
    updated = 0
    errors = []

    with transaction.atomic():
        for c in session.codes_staged:
            try:
                code_val = str(c["code"]).strip().upper()
                defaults = {
                    "label": c.get("label", ""),
                    "excused": bool(c.get("excused", False)),
                    "counts_as_tardy": bool(c.get("counts_as_tardy", False)),
                    "counts_as_absent": bool(c.get("counts_as_absent", True)),
                    "notify_guardian": bool(c.get("notify_guardian", False)),
                }
                _, was_created = AttendanceCode.objects.update_or_create(
                    school_id=school_id,
                    code=code_val,
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
        session.status = AttendanceCodesWizardSession.STATUS_COMMITTED
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
        AttendanceCodesWizardSession.STATUS_COMMITTED,
        AttendanceCodesWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Session must be committed before verify (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from attendance.models import AttendanceCode
    code_count = AttendanceCode.objects.filter(school_id=school_id).count()

    if session.status == AttendanceCodesWizardSession.STATUS_COMMITTED:
        session.status = AttendanceCodesWizardSession.STATUS_VERIFIED
        session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "active_code_count": code_count,
        **(session.commit_result or {}),
    })
