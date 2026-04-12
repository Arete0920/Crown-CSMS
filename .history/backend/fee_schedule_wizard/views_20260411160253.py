"""
fee_schedule_wizard/views.py

5 endpoints for the Fee Schedule Setup Wizard:

  POST /api/v1/fee-schedule-wizard/sessions/                         → create_session
  POST /api/v1/fee-schedule-wizard/sessions/<id>/configure/          → configure_session
  POST /api/v1/fee-schedule-wizard/sessions/<id>/lines/              → set_lines
  POST /api/v1/fee-schedule-wizard/sessions/<id>/commit/             → commit_session
  GET  /api/v1/fee-schedule-wizard/sessions/<id>/verify/             → verify_session

Auth: JWT or Session. All endpoints tenant-scoped via X-School-Id.
"""
import re
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from audit.models import AuditLog
from core.models import School
from households.scoping import get_request_school_id

from .models import FeeSchedule, FeeScheduleWizardSession, FeeLine

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)

VALID_KINDS  = {c[0] for c in FeeLine.KIND_CHOICES}
VALID_FREQS  = {c[0] for c in FeeLine.FREQ_CHOICES}
_CODE_RE     = re.compile(r'^[A-Za-z0-9_-]{1,32}$')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(FeeScheduleWizardSession, id=session_id, school_id=school_id)


def _validate_line(line, idx):
    errors = []
    code  = (line.get("code")  or "").strip()
    label = (line.get("label") or "").strip()

    if not code:
        errors.append(f"lines[{idx}].code is required")
    elif not _CODE_RE.match(code):
        errors.append(f"lines[{idx}].code must be alphanumeric/underscore/hyphen, max 32 chars")

    if not label:
        errors.append(f"lines[{idx}].label is required")

    try:
        amount = int(line.get("amount_cents", -1))
        if amount < 0:
            errors.append(f"lines[{idx}].amount_cents must be a non-negative integer")
    except (TypeError, ValueError):
        errors.append(f"lines[{idx}].amount_cents must be an integer (cents)")

    kind = (line.get("kind") or "").strip()
    if kind and kind not in VALID_KINDS:
        errors.append(f"lines[{idx}].kind must be one of: {sorted(VALID_KINDS)}")

    freq = (line.get("frequency") or "").strip()
    if freq and freq not in VALID_FREQS:
        errors.append(f"lines[{idx}].frequency must be one of: {sorted(VALID_FREQS)}")

    return errors


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school    = get_object_or_404(School, id=school_id)
    session   = FeeScheduleWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure — name, term, effective_date
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    name           = (request.data.get("name")           or "").strip()
    term           = (request.data.get("term")           or "").strip()
    effective_date = (request.data.get("effective_date") or "").strip()

    errors = []
    if not name:
        errors.append("name is required")
    if not term:
        errors.append("term is required")
    if not effective_date:
        errors.append("effective_date is required (YYYY-MM-DD)")
    else:
        # Basic date format validation
        import datetime
        try:
            datetime.date.fromisoformat(effective_date)
        except ValueError:
            errors.append("effective_date must be a valid date (YYYY-MM-DD)")

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.schedule_name  = name
    session.term           = term
    session.effective_date = effective_date
    session.status         = FeeScheduleWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({"session_id": str(session.id), "status": session.status})


# ---------------------------------------------------------------------------
# 3. Lines — define fee lines
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_lines(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status == FeeScheduleWizardSession.STATUS_DRAFT:
        return Response(
            {"error": "Session must be configured before setting lines"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    lines = request.data.get("lines")
    if not isinstance(lines, list) or len(lines) == 0:
        return Response(
            {"error": "lines must be a non-empty list"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate all lines; collect all errors before returning
    all_errors = []
    for idx, line in enumerate(lines):
        all_errors.extend(_validate_line(line, idx))

    if all_errors:
        return Response({"errors": all_errors}, status=status.HTTP_400_BAD_REQUEST)

    # Dedup check on code within the submitted batch
    codes = [l.get("code", "").strip() for l in lines]
    if len(codes) != len(set(codes)):
        return Response(
            {"error": "duplicate codes in lines — each code must be unique within a schedule"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.lines_config = lines
    session.status       = FeeScheduleWizardSession.STATUS_LINES_SET
    session.save()

    return Response({
        "session_id":  str(session.id),
        "status":      session.status,
        "lines_count": len(lines),
    })


# ---------------------------------------------------------------------------
# 4. Commit — create FeeSchedule + FeeLine records
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    committable = {
        FeeScheduleWizardSession.STATUS_LINES_SET,
    }
    if session.status not in committable:
        return Response(
            {"error": f"session must be in lines_set state before commit (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        schedule, sched_created = FeeSchedule.objects.get_or_create(
            school_id=school_id,
            name=session.schedule_name,
            defaults={
                "term":           session.term,
                "effective_date": session.effective_date,
                "is_active":      True,
            },
        )

        # Ensure this schedule is active (covers idempotent re-commit)
        if not schedule.is_active:
            schedule.is_active = True
            schedule.save(update_fields=["is_active"])

        # Single-active enforcement: exactly one active FeeSchedule per school
        deactivated_count = (
            FeeSchedule.objects
            .filter(school_id=school_id)
            .exclude(pk=schedule.pk)
            .update(is_active=False)
        )

        lines_created = 0
        lines_updated = 0
        for idx, lc in enumerate(session.lines_config):
            code     = lc.get("code", "").strip()
            defaults = {
                "label":       (lc.get("label") or "").strip(),
                "amount_cents": int(lc.get("amount_cents", 0)),
                "kind":         (lc.get("kind")      or FeeLine.KIND_FEE).strip(),
                "frequency":    (lc.get("frequency") or FeeLine.FREQ_ANNUAL).strip(),
                "is_required":  bool(lc.get("is_required", True)),
                "sort_order":   int(lc.get("sort_order", idx)),
            }
            _, line_created = FeeLine.objects.update_or_create(
                fee_schedule=schedule,
                code=code,
                defaults=defaults,
            )
            if line_created:
                lines_created += 1
            else:
                lines_updated += 1

        result = {
            "schedule_id":   str(schedule.id),
            "schedule_name": schedule.name,
            "term":          schedule.term,
            "created":       sched_created,
            "lines_created": lines_created,
            "lines_updated": lines_updated,
            "deactivated_count": deactivated_count,
            "message": (
                "Fee schedule created with {} line(s).".format(lines_created + lines_updated)
                if sched_created
                else "Fee schedule already existed; {} line(s) updated, {} new.".format(lines_updated, lines_created)
            ),
        }
        session.commit_result = result
        session.status        = FeeScheduleWizardSession.STATUS_COMMITTED
        session.save()

    # Audit log — non-fatal
    try:
        AuditLog.objects.create(
            user_id=getattr(request.user, "id", None),
            action="fee_schedule.commit",
            model="FeeSchedule",
            object_id=result["schedule_id"],
            metadata={
                "schedule_name": result["schedule_name"],
                "term":          result["term"],
                "created":       result["created"],
                "lines_created":    result["lines_created"],
                "lines_updated":    result["lines_updated"],
                "deactivated_count": result["deactivated_count"],
                "school_id":        str(school_id),
                "session_id":       str(session.id),
            },
        )
    except Exception as exc:
        logger.warning("fee_schedule.commit audit log skipped: %s", exc)

    return Response({"session_id": str(session.id), "status": session.status, "result": result})


# ---------------------------------------------------------------------------
# 5. Verify — confirm FeeSchedule + line count
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status != FeeScheduleWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": "session must be committed before verify"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    schedule_exists = FeeSchedule.objects.filter(
        school_id=school_id, name=session.schedule_name
    ).exists()

    line_count = 0
    if schedule_exists:
        schedule   = FeeSchedule.objects.get(school_id=school_id, name=session.schedule_name)
        line_count = schedule.lines.count()

    session.status = FeeScheduleWizardSession.STATUS_VERIFIED
    session.save(update_fields=["status", "updated_at"])

    return Response({
        "session_id":      str(session.id),
        "status":          session.status,
        "schedule_exists": schedule_exists,
        "schedule_name":   session.schedule_name,
        "line_count":      line_count,
    })
