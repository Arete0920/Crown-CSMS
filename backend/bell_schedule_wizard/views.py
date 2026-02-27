from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id

from .models import BellScheduleWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


def _get_session(session_id, school_id):
    return get_object_or_404(BellScheduleWizardSession, id=session_id, school__id=school_id)


def _validate_time(value, field_name):
    """Validate HH:MM format."""
    if not value or not isinstance(value, str):
        return f"{field_name} is required"
    parts = value.split(":")
    if len(parts) != 2:
        return f"{field_name} must be HH:MM"
    try:
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return f"{field_name} must be a valid time (00:00-23:59)"
    except ValueError:
        return f"{field_name} must be HH:MM"
    return None


def _validate_period(period, idx):
    errors = []
    name = (period.get("name") or "").strip()
    if not name:
        errors.append(f"periods[{idx}].name is required")
    err = _validate_time(period.get("start_time"), f"periods[{idx}].start_time")
    if err:
        errors.append(err)
    err = _validate_time(period.get("end_time"), f"periods[{idx}].end_time")
    if err:
        errors.append(err)
    days = period.get("days")
    if days is not None:
        if not isinstance(days, list):
            errors.append(f"periods[{idx}].days must be a list")
        else:
            invalid = [d for d in days if d not in VALID_DAYS]
            if invalid:
                errors.append(f"periods[{idx}].days contains invalid values: {invalid}")
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
    session = BellScheduleWizardSession.objects.create(
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
    if len(label) > 128:
        return Response({"error": "label must be 128 characters or fewer"}, status=status.HTTP_400_BAD_REQUEST)

    school_year = (request.data.get("school_year") or "").strip()
    if not school_year:
        return Response({"error": "school_year is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.label = label
    session.school_year = school_year
    session.status = BellScheduleWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "label": label, "school_year": school_year})


# ---------------------------------------------------------------------------
# 3. Define periods
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def define_periods(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        BellScheduleWizardSession.STATUS_CONFIGURED,
        BellScheduleWizardSession.STATUS_PERIODS_DEFINED,
    ):
        return Response(
            {"error": f"Cannot define periods from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    periods_raw = request.data.get("periods")
    if not isinstance(periods_raw, list) or len(periods_raw) == 0:
        return Response({"error": "periods must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    for idx, p in enumerate(periods_raw):
        errors.extend(_validate_period(p, idx))
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    cleaned = [
        {
            "name": p["name"].strip(),
            "start_time": p["start_time"],
            "end_time": p["end_time"],
            "days": p.get("days") or ["Mon", "Tue", "Wed", "Thu", "Fri"],
        }
        for p in periods_raw
    ]

    session.periods = cleaned
    session.status = BellScheduleWizardSession.STATUS_PERIODS_DEFINED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "period_count": len(cleaned)})


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
        BellScheduleWizardSession.STATUS_PERIODS_DEFINED,
        BellScheduleWizardSession.STATUS_COMMITTED,
    ):
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        result = {
            "period_count": len(session.periods),
            "label": session.label,
            "school_year": session.school_year,
        }
        session.commit_result = result
        session.status = BellScheduleWizardSession.STATUS_COMMITTED
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
        BellScheduleWizardSession.STATUS_COMMITTED,
        BellScheduleWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.status = BellScheduleWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "status": session.status,
        "period_count": len(session.periods),
        "label": session.label,
        "school_year": session.school_year,
        "commit_result": session.commit_result,
    })
