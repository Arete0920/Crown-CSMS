from datetime import time
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id

from .models import (
    BellSchedule,
    BellScheduleWizardSession,
    DayTemplate,
    PeriodBlock,
    VALID_SCHEDULE_MODES,
)

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(BellScheduleWizardSession, id=session_id, school__id=school_id)


def _parse_time(value, field_name):
    """Parse "HH:MM" → datetime.time.  Returns (time | None, error_str | None)."""
    if not value or not isinstance(value, str):
        return None, f"{field_name} is required"
    try:
        parts = value.strip().split(":")
        if len(parts) != 2:
            raise ValueError
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return time(h, m), None
    except (ValueError, AttributeError):
        return None, f"{field_name} must be HH:MM (e.g. 08:00)"


def _validate_blocks_for_template(template_code, raw_blocks):
    """
    Validate and sort blocks for one template.
    Invariants: code+label required, codes unique, start < end, no overlap (gaps OK).
    Returns (errors: list[str], validated: list[dict] | None).
    """
    errors = []
    if not isinstance(raw_blocks, list) or len(raw_blocks) == 0:
        return [f"template '{template_code}': blocks must be a non-empty list"], None

    parsed    = []
    seen_codes = set()

    for i, block in enumerate(raw_blocks):
        code = (block.get("code") or "").strip()
        if not code:
            errors.append(f"template '{template_code}' block[{i}].code is required")
        elif code in seen_codes:
            errors.append(f"template '{template_code}': duplicate block code '{code}'")
        else:
            seen_codes.add(code)

        label = (block.get("label") or "").strip()
        if not label:
            errors.append(f"template '{template_code}' block[{i}].label is required")

        st, err = _parse_time(block.get("start_time"), f"template '{template_code}' block[{i}].start_time")
        if err:
            errors.append(err)

        et, err = _parse_time(block.get("end_time"), f"template '{template_code}' block[{i}].end_time")
        if err:
            errors.append(err)

        if st and et and st >= et:
            errors.append(
                f"template '{template_code}' block '{code or i}': start_time must be before end_time"
            )

        parsed.append({
            "code":             code,
            "label":            label,
            "start_time":       st,
            "end_time":         et,
            "is_instructional": bool(block.get("is_instructional", False)),
            "is_lunch":         bool(block.get("is_lunch", False)),
            "is_break":         bool(block.get("is_break", False)),
        })

    if errors:
        return errors, None

    # Sort by start_time, assign ordering
    parsed.sort(key=lambda b: b["start_time"])
    for i, b in enumerate(parsed):
        b["ordering"] = i

    # Overlap check (gaps are allowed per canon)
    for i in range(len(parsed) - 1):
        a, b = parsed[i], parsed[i + 1]
        if b["start_time"] < a["end_time"]:
            errors.append(
                f"template '{template_code}': overlap between block '{a['code']}' and '{b['code']}'"
            )

    if errors:
        return errors, None

    return [], parsed


def _blocks_to_json(validated_blocks):
    """Convert time objects → HH:MM strings for JSONField storage."""
    result = []
    for b in validated_blocks:
        entry = dict(b)
        entry["start_time"] = b["start_time"].strftime("%H:%M")
        entry["end_time"]   = b["end_time"].strftime("%H:%M")
        result.append(entry)
    return result


def _blocks_from_json(stored_blocks):
    """Convert HH:MM strings → time objects for commit."""
    result = []
    for b in stored_blocks:
        entry = dict(b)
        hs, ms = b["start_time"].split(":")
        he, me = b["end_time"].split(":")
        entry["start_time"] = time(int(hs), int(ms))
        entry["end_time"]   = time(int(he), int(me))
        result.append(entry)
    return result


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
    session   = _get_session(session_id, school_id)

    schedule_name = (request.data.get("schedule_name") or "").strip()
    if not schedule_name:
        return Response({"error": "schedule_name is required"}, status=status.HTTP_400_BAD_REQUEST)
    if len(schedule_name) > 100:
        return Response({"error": "schedule_name must be 100 characters or fewer"}, status=status.HTTP_400_BAD_REQUEST)

    schedule_mode = (request.data.get("schedule_mode") or "").strip().upper()
    if not schedule_mode:
        return Response({"error": "schedule_mode is required"}, status=status.HTTP_400_BAD_REQUEST)
    if schedule_mode not in VALID_SCHEDULE_MODES:
        return Response(
            {"error": f"schedule_mode must be one of: {sorted(VALID_SCHEDULE_MODES)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ay_id = request.data.get("academic_year_id")
    if not ay_id:
        return Response({"error": "academic_year_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    from core.models import AcademicYear
    ay = get_object_or_404(AcademicYear, id=ay_id, school=session.school)

    session.schedule_name = schedule_name
    session.schedule_mode = schedule_mode
    session.academic_year = ay
    session.status        = BellScheduleWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id":       str(session.id),
        "status":           session.status,
        "schedule_name":    session.schedule_name,
        "schedule_mode":    session.schedule_mode,
        "academic_year_id": str(ay.id),
    })


# ---------------------------------------------------------------------------
# 3. Set Blocks
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_blocks(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status not in (
        BellScheduleWizardSession.STATUS_CONFIGURED,
        BellScheduleWizardSession.STATUS_BLOCKS_SET,
    ):
        return Response(
            {"error": f"Session must be 'configured' or 'blocks_set'; current: {session.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_templates = request.data.get("templates")
    if not isinstance(raw_templates, list) or len(raw_templates) == 0:
        return Response({"error": "templates must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    # Template code uniqueness
    seen_template_codes = set()
    for i, tpl in enumerate(raw_templates):
        tc = (tpl.get("template_code") or "").strip().upper()
        if not tc:
            return Response(
                {"error": f"templates[{i}].template_code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if tc in seen_template_codes:
            return Response(
                {"error": f"Duplicate template_code: '{tc}'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        seen_template_codes.add(tc)

    # Mode-specific count validation
    if session.schedule_mode == "SINGLE_DAY":
        if len(raw_templates) != 1:
            return Response(
                {"error": "SINGLE_DAY schedule requires exactly 1 template"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if list(seen_template_codes)[0] != "DEFAULT":
            return Response(
                {"error": "SINGLE_DAY schedule template_code must be 'DEFAULT'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif session.schedule_mode == "DAY_TEMPLATES":
        if len(raw_templates) < 2:
            return Response(
                {"error": "DAY_TEMPLATES schedule requires at least 2 templates"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Validate each template's blocks
    all_errors     = []
    validated_tpls = []
    for tpl in raw_templates:
        tc         = tpl.get("template_code", "").strip().upper()
        raw_blocks = tpl.get("blocks", [])
        errs, validated_blocks = _validate_blocks_for_template(tc, raw_blocks)
        if errs:
            all_errors.extend(errs)
        else:
            validated_tpls.append({"template_code": tc, "blocks": _blocks_to_json(validated_blocks)})

    if all_errors:
        return Response({"errors": all_errors}, status=status.HTTP_400_BAD_REQUEST)

    session.blocks_config = validated_tpls
    session.status        = BellScheduleWizardSession.STATUS_BLOCKS_SET
    session.save()

    return Response({
        "session_id":     str(session.id),
        "status":         session.status,
        "template_count": len(validated_tpls),
    })


# ---------------------------------------------------------------------------
# 4. Commit
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status != BellScheduleWizardSession.STATUS_BLOCKS_SET:
        return Response(
            {"error": f"Session must be 'blocks_set' to commit; current: {session.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    school        = session.school
    academic_year = session.academic_year
    blocks_config = session.blocks_config

    with transaction.atomic():
        # Lock all schedules for this school/year, then flip active → inactive
        list(BellSchedule.objects.select_for_update().filter(school=school, academic_year=academic_year))
        BellSchedule.objects.filter(school=school, academic_year=academic_year, is_active=True).update(
            is_active=False
        )

        # Idempotent get_or_create by (school, academic_year, name)
        schedule, created = BellSchedule.objects.get_or_create(
            school=school,
            academic_year=academic_year,
            name=session.schedule_name,
            defaults={"schedule_mode": session.schedule_mode, "is_active": False},
        )
        if not created:
            schedule.schedule_mode = session.schedule_mode
        schedule.is_active = True
        schedule.save()

        template_summaries     = []
        current_template_codes = set()

        for i, tpl_data in enumerate(blocks_config):
            tc            = tpl_data["template_code"]
            current_template_codes.add(tc)
            stored_blocks = _blocks_from_json(tpl_data["blocks"])

            template, _ = DayTemplate.objects.update_or_create(
                schedule=schedule,
                template_code=tc,
                defaults={"ordering": i},
            )

            current_block_codes = set()
            for block_data in stored_blocks:
                PeriodBlock.objects.update_or_create(
                    template=template,
                    code=block_data["code"],
                    defaults={
                        "label":            block_data["label"],
                        "start_time":       block_data["start_time"],
                        "end_time":         block_data["end_time"],
                        "ordering":         block_data["ordering"],
                        "is_instructional": block_data.get("is_instructional", False),
                        "is_lunch":         block_data.get("is_lunch", False),
                        "is_break":         block_data.get("is_break", False),
                    },
                )
                current_block_codes.add(block_data["code"])

            # Delete stale blocks scoped to this template
            PeriodBlock.objects.filter(template=template).exclude(code__in=current_block_codes).delete()

            template_summaries.append({
                "template_code": tc,
                "block_count":   len(stored_blocks),
                "blocks": [
                    {
                        "code":       b["code"],
                        "start_time": b["start_time"].strftime("%H:%M"),
                        "end_time":   b["end_time"].strftime("%H:%M"),
                        "ordering":   b["ordering"],
                    }
                    for b in stored_blocks
                ],
            })

        # Delete stale templates scoped to this schedule
        DayTemplate.objects.filter(schedule=schedule).exclude(
            template_code__in=current_template_codes
        ).delete()

    # Audit event (non-fatal)
    try:
        from crown_api.audit import log_event
        log_event(
            event="bell_schedule.commit",
            school_id=str(school.id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
            payload={"schedule_id": str(schedule.id), "name": schedule.name},
        )
    except Exception:
        logger.exception("commit_session: bell schedule audit event failed")

    result = {
        "schedule_id":      str(schedule.id),
        "schedule_name":    schedule.name,
        "schedule_mode":    schedule.schedule_mode,
        "is_active":        schedule.is_active,
        "academic_year_id": str(academic_year.id),
        "templates":        template_summaries,
    }
    session.commit_result = result
    session.status        = BellScheduleWizardSession.STATUS_COMMITTED
    session.save()

    return Response(result)


# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status != BellScheduleWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": "Session must be committed before verifying"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result      = session.commit_result or {}
    schedule_id = result.get("schedule_id")
    if not schedule_id:
        return Response({"error": "No commit_result; re-commit session"}, status=status.HTTP_400_BAD_REQUEST)

    schedule  = get_object_or_404(BellSchedule, id=schedule_id, school=session.school)
    templates = DayTemplate.objects.filter(schedule=schedule).prefetch_related("blocks").order_by("ordering")

    snapshot = []
    for tpl in templates:
        blocks = list(tpl.blocks.order_by("ordering"))
        snapshot.append({
            "template_code": tpl.template_code,
            "blocks": [
                {
                    "code":       b.code,
                    "start_time": b.start_time.strftime("%H:%M"),
                    "end_time":   b.end_time.strftime("%H:%M"),
                    "ordering":   b.ordering,
                }
                for b in blocks
            ],
        })

    session.status = BellScheduleWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "schedule_id":    str(schedule.id),
        "schedule_name":  schedule.name,
        "schedule_mode":  schedule.schedule_mode,
        "is_active":      schedule.is_active,
        "template_count": len(snapshot),
        "snapshot":       snapshot,
    })
