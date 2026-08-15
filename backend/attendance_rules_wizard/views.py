from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from attendance_codes_wizard.models import AttendanceCode, AttendanceConfiguration
from core.permissions import user_has_permission
from households.scoping import get_request_school_id

from .models import AttendanceRulesWizardSession
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _authorized_school(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    if not user_has_permission(request.user, "attendance.configure", school=school):
        raise PermissionDenied("You do not have permission to configure attendance.")
    return school


def _get_session(session_id, school_id):
    return get_object_or_404(AttendanceRulesWizardSession, id=session_id, school__id=school_id)


def _validate_code(code_obj, idx):
    if not isinstance(code_obj, dict):
        return [f"codes[{idx}] must be an object"]
    errors = []
    code = str(code_obj.get("code") or "").strip().upper()
    if not code:
        errors.append(f"codes[{idx}].code is required")
    elif len(code) > 8:
        errors.append(f"codes[{idx}].code must be 8 characters or fewer")
    if not str(code_obj.get("label") or "").strip():
        errors.append(f"codes[{idx}].label is required")
    return errors


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school = _authorized_school(request)
    session = AttendanceRulesWizardSession.objects.create(school=school, created_by=request.user)
    return Response({"session_id": str(session.id), "status": session.status}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status in (AttendanceRulesWizardSession.STATUS_COMMITTED, AttendanceRulesWizardSession.STATUS_VERIFIED):
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)
    label = str(request.data.get("label") or "").strip()
    school_year = str(request.data.get("school_year") or "").strip()
    if not label or not school_year:
        return Response({"error": "label and school_year are required"}, status=status.HTTP_400_BAD_REQUEST)
    session.label = label
    session.school_year = school_year
    session.status = AttendanceRulesWizardSession.STATUS_CONFIGURED
    session.save(update_fields=["label", "school_year", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "label": label, "school_year": school_year})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def define_codes(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status not in (AttendanceRulesWizardSession.STATUS_CONFIGURED, AttendanceRulesWizardSession.STATUS_CODES_DEFINED):
        return Response({"error": f"Cannot define codes from status '{session.status}'"}, status=status.HTTP_400_BAD_REQUEST)
    codes_raw = request.data.get("codes")
    if not isinstance(codes_raw, list) or not codes_raw:
        return Response({"error": "codes must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
    errors = []
    for idx, code in enumerate(codes_raw):
        errors.extend(_validate_code(code, idx))
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    seen = {}
    for item in codes_raw:
        seen[str(item["code"]).strip().upper()] = item
    cleaned = [{
        "code": code,
        "label": str(data["label"]).strip(),
        "excused": bool(data.get("excused", False)),
        "counts_as_tardy": bool(data.get("counts_as_tardy", False)),
        "counts_as_absent": bool(data.get("counts_as_absent", data.get("counts_absent", False))),
        "notify_guardian": bool(data.get("notify_guardian", False)),
    } for code, data in seen.items()]
    session.codes = cleaned
    session.status = AttendanceRulesWizardSession.STATUS_CODES_DEFINED
    session.save(update_fields=["codes", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "code_count": len(cleaned)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status in (AttendanceRulesWizardSession.STATUS_COMMITTED, AttendanceRulesWizardSession.STATUS_VERIFIED):
        return Response({"status": session.status, **(session.commit_result or {})})
    if session.status != AttendanceRulesWizardSession.STATUS_CODES_DEFINED:
        return Response({"error": f"Cannot commit from status '{session.status}'"}, status=status.HTTP_400_BAD_REQUEST)
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        configuration, _ = AttendanceConfiguration.objects.update_or_create(
            school=school,
            school_year=session.school_year,
            defaults={"label": session.label, "policy_config": {"school_year": session.school_year}, "is_active": True, "updated_by": request.user},
        )
        active_codes = set()
        for item in session.codes:
            active_codes.add(item["code"])
            AttendanceCode.objects.update_or_create(configuration=configuration, code=item["code"], defaults={**item, "is_active": True})
        AttendanceCode.objects.filter(configuration=configuration).exclude(code__in=active_codes).update(is_active=False)
        persisted_count = AttendanceCode.objects.filter(configuration=configuration, is_active=True).count()
        if persisted_count != len(session.codes):
            raise RuntimeError("Canonical attendance rules reread count mismatch")
        result = {"configuration_id": str(configuration.id), "code_count": persisted_count, "label": configuration.label, "school_year": configuration.school_year}
        session.commit_result = result
        session.status = AttendanceRulesWizardSession.STATUS_COMMITTED
        session.save(update_fields=["commit_result", "status", "updated_at"])
    return Response({"status": session.status, **result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school = _authorized_school(request)
    session = _get_session(session_id, school.id)
    if session.status not in (AttendanceRulesWizardSession.STATUS_COMMITTED, AttendanceRulesWizardSession.STATUS_VERIFIED):
        return Response({"error": f"Cannot verify from status '{session.status}'"}, status=status.HTTP_400_BAD_REQUEST)
    result = session.commit_result or {}
    configuration = get_object_or_404(AttendanceConfiguration, id=result.get("configuration_id"), school=school, school_year=session.school_year, is_active=True)
    code_count = AttendanceCode.objects.filter(configuration=configuration, is_active=True).count()
    if code_count != result.get("code_count"):
        return Response({"error": "Canonical attendance rules verification failed"}, status=status.HTTP_409_CONFLICT)
    if session.status == AttendanceRulesWizardSession.STATUS_COMMITTED:
        session.status = AttendanceRulesWizardSession.STATUS_VERIFIED
        session.save(update_fields=["status", "updated_at"])
    return Response({"status": session.status, "code_count": code_count, "label": configuration.label, "school_year": configuration.school_year, "commit_result": result})
