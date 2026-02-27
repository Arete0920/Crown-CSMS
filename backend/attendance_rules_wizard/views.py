from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id

from .models import AttendanceRulesWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(AttendanceRulesWizardSession, id=session_id, school__id=school_id)


def _validate_code(code_obj, idx):
    errors = []
    code = (code_obj.get("code") or "").strip().upper()
    if not code:
        errors.append(f"codes[{idx}].code is required")
    elif len(code) > 8:
        errors.append(f"codes[{idx}].code must be 8 characters or fewer")
    label = (code_obj.get("label") or "").strip()
    if not label:
        errors.append(f"codes[{idx}].label is required")
    return errors


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = AttendanceRulesWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({"session_id": str(session.id), "status": session.status}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# 2. Configure
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    label = (request.data.get("label") or "").strip()
    if not label:
        return Response({"error": "label is required"}, status=status.HTTP_400_BAD_REQUEST)

    school_year = (request.data.get("school_year") or "").strip()
    if not school_year:
        return Response({"error": "school_year is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.label = label
    session.school_year = school_year
    session.status = AttendanceRulesWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "label": label, "school_year": school_year})


# ---------------------------------------------------------------------------
# 3. Define codes
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def define_codes(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        AttendanceRulesWizardSession.STATUS_CONFIGURED,
        AttendanceRulesWizardSession.STATUS_CODES_DEFINED,
    ):
        return Response(
            {"error": f"Cannot define codes from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    codes_raw = request.data.get("codes")
    if not isinstance(codes_raw, list) or len(codes_raw) == 0:
        return Response({"error": "codes must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    for idx, c in enumerate(codes_raw):
        errors.extend(_validate_code(c, idx))
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    # Deduplicate by code (last definition wins)
    seen = {}
    for c in codes_raw:
        seen[c["code"].strip().upper()] = c
    cleaned = [
        {
            "code": code,
            "label": data["label"].strip(),
            "excused": bool(data.get("excused", False)),
            "counts_absent": bool(data.get("counts_absent", False)),
        }
        for code, data in seen.items()
    ]

    session.codes = cleaned
    session.status = AttendanceRulesWizardSession.STATUS_CODES_DEFINED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "code_count": len(cleaned)})


# ---------------------------------------------------------------------------
# 4. Commit
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        AttendanceRulesWizardSession.STATUS_CODES_DEFINED,
        AttendanceRulesWizardSession.STATUS_COMMITTED,
    ):
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        result = {
            "code_count": len(session.codes),
            "label": session.label,
            "school_year": session.school_year,
        }
        session.commit_result = result
        session.status = AttendanceRulesWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"status": session.status, **result})


# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        AttendanceRulesWizardSession.STATUS_COMMITTED,
        AttendanceRulesWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.status = AttendanceRulesWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "status": session.status,
        "code_count": len(session.codes),
        "label": session.label,
        "school_year": session.school_year,
        "commit_result": session.commit_result,
    })
