from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.permissions import user_has_permission
from households.scoping import get_request_school_id

from .models import AttendanceCode, AttendanceCodesWizardSession, AttendanceConfiguration
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
REQUIRED_CODE_FIELDS = {"code", "label"}


def _authorized_school(request):
    school_id = get_request_school_id(request)
    from core.models import School

    school = get_object_or_404(School, id=school_id)
    if not user_has_permission(request.user, "attendance.configure", school=school):
        raise PermissionDenied("You do not have permission to configure attendance.")
    return school


def _get_session(session_id, school_id):
    return get_object_or_404(AttendanceCodesWizardSession, id=session_id, school__id=school_id)


def _normalize_codes(codes):
    normalized = []
    seen_codes = set()
    for i, raw in enumerate(codes):
        if not isinstance(raw, dict):
            raise ValueError(f"codes_staged[{i}] must be an object")
        missing = REQUIRED_CODE_FIELDS - set(raw.keys())
        if missing:
            raise ValueError(f"codes_staged[{i}] missing fields: {sorted(missing)}")
        code = str(raw["code"]).strip().upper()
        label = str(raw["label"]).strip()
        if not code:
            raise ValueError(f"codes_staged[{i}].code must not be empty")
        if len(code) > 8:
            raise ValueError(f"codes_staged[{i}].code must be 8 characters or fewer")
        if not label:
            raise ValueError(f"codes_staged[{i}].label must not be empty")
        if code in seen_codes:
            raise ValueError(f"Duplicate code: '{code}'")
        seen_codes.add(code)
        normalized.append({
            "code": code,
            "label": label,
            "excused": bool(raw.get("excused", False)),
            "counts_as_tardy": bool(raw.get("counts_as_tardy", False)),
            "counts_as_absent": bool(raw.get("counts_as_absent", False)),
            "notify_guardian": bool(raw.get("notify_guardian", False)),
        })
    return normalized


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school = _authorized_school(request)
    session = AttendanceCodesWizardSession.objects.create(school=school, created_by=request.user)
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status in (AttendanceCodesWizardSession.STATUS_COMMITTED, AttendanceCodesWizardSession.STATUS_VERIFIED):
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)
    policy_config = request.data.get("policy_config")
    if not isinstance(policy_config, dict):
        return Response({"error": "policy_config must be an object"}, status=status.HTTP_400_BAD_REQUEST)
    school_year = str(policy_config.get("school_year", "")).strip()
    if not school_year:
        return Response({"error": "policy_config.school_year is required"}, status=status.HTTP_400_BAD_REQUEST)
    session.policy_config = policy_config
    session.status = AttendanceCodesWizardSession.STATUS_CONFIGURED
    session.save(update_fields=["policy_config", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_codes(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status != AttendanceCodesWizardSession.STATUS_CONFIGURED:
        return Response({"error": f"Session must be in 'configured' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    codes = request.data.get("codes_staged")
    if not isinstance(codes, list) or not codes:
        return Response({"error": "codes_staged must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        normalized = _normalize_codes(codes)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    session.codes_staged = normalized
    session.status = AttendanceCodesWizardSession.STATUS_CODES_STAGED
    session.save(update_fields=["codes_staged", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "code_count": len(normalized)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status in (AttendanceCodesWizardSession.STATUS_COMMITTED, AttendanceCodesWizardSession.STATUS_VERIFIED):
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
    if session.status != AttendanceCodesWizardSession.STATUS_CODES_STAGED:
        return Response({"error": f"Session must be in 'codes_staged' state (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    school_year = str(session.policy_config.get("school_year", "")).strip()
    if not school_year:
        return Response({"error": "Configured school_year is required"}, status=status.HTTP_400_BAD_REQUEST)
    normalized = _normalize_codes(session.codes_staged)

    with transaction.atomic():
        configuration, _ = AttendanceConfiguration.objects.update_or_create(
            school=school,
            school_year=school_year,
            defaults={
                "label": str(session.policy_config.get("label") or "Attendance Policy").strip() or "Attendance Policy",
                "policy_config": session.policy_config,
                "is_active": True,
                "updated_by": request.user,
            },
        )
        submitted_codes = {item["code"] for item in normalized}
        AttendanceCode.objects.filter(configuration=configuration).exclude(code__in=submitted_codes).update(is_active=False)
        created = 0
        updated = 0
        for item in normalized:
            _, was_created = AttendanceCode.objects.update_or_create(
                configuration=configuration,
                code=item["code"],
                defaults={**item, "is_active": True},
            )
            created += int(was_created)
            updated += int(not was_created)
        persisted_count = AttendanceCode.objects.filter(configuration=configuration, is_active=True).count()
        if persisted_count != len(normalized):
            raise RuntimeError("Canonical attendance configuration reread count mismatch")
        result = {
            "configuration_id": str(configuration.id),
            "school_year": school_year,
            "created": created,
            "updated": updated,
            "active_code_count": persisted_count,
        }
        session.commit_result = result
        session.status = AttendanceCodesWizardSession.STATUS_COMMITTED
        session.save(update_fields=["commit_result", "status", "updated_at"])

    return Response({"session_id": str(session.id), "status": session.status, **result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status not in (AttendanceCodesWizardSession.STATUS_COMMITTED, AttendanceCodesWizardSession.STATUS_VERIFIED):
        return Response({"error": f"Session must be committed before verify (current: {session.status})"}, status=status.HTTP_400_BAD_REQUEST)
    result = session.commit_result or {}
    configuration = get_object_or_404(
        AttendanceConfiguration,
        id=result.get("configuration_id"),
        school=school,
        school_year=result.get("school_year"),
        is_active=True,
    )
    code_count = AttendanceCode.objects.filter(configuration=configuration, is_active=True).count()
    if code_count != result.get("active_code_count"):
        return Response({"error": "Canonical attendance configuration verification failed"}, status=status.HTTP_409_CONFLICT)
    if session.status == AttendanceCodesWizardSession.STATUS_COMMITTED:
        session.status = AttendanceCodesWizardSession.STATUS_VERIFIED
        session.save(update_fields=["status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "active_code_count": code_count, **result})
