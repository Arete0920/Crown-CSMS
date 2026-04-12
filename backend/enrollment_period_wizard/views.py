"""
enrollment_period_wizard/views.py

5 endpoints for the Enrollment Period Setup Wizard (#16):

  POST /api/v1/enrollment-period-wizard/sessions/                         → create_session
  POST /api/v1/enrollment-period-wizard/sessions/<id>/configure/          → configure_session
  POST /api/v1/enrollment-period-wizard/sessions/<id>/capacities/         → set_capacities
  POST /api/v1/enrollment-period-wizard/sessions/<id>/commit/             → commit_session
  GET  /api/v1/enrollment-period-wizard/sessions/<id>/verify/             → verify_session

Auth: JWT or Session. All endpoints tenant-scoped via X-School-Id.

Commit:
  - select_for_update on EnrollmentPeriod rows for (school, academic_year) to serialize races
  - get_or_create EnrollmentPeriod; update fields on re-commit (idempotent)
  - update_or_create GradeCapacity per grade_code
  - DB constraints ensure uniqueness even under concurrency
"""
import datetime
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
from core.models import AcademicYear, School
from households.scoping import get_request_school_id

from .models import (
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
    EnrollmentPeriod,
    EnrollmentPeriodWizardSession,
    GradeCapacity,
    VALID_GRADE_CODES,
)

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(EnrollmentPeriodWizardSession, id=session_id, school_id=school_id)


def _parse_date(value, field_name):
    """Return (date_obj_or_None, error_str_or_None)."""
    if not value:
        return None, f"{field_name} is required"
    try:
        return datetime.date.fromisoformat(str(value).strip()), None
    except ValueError:
        return None, f"{field_name} must be a valid ISO date (YYYY-MM-DD)"


def _validate_capacity(cap, idx):
    errors = []
    grade_code = (cap.get("grade_code") or "").strip()
    if not grade_code:
        errors.append(f"capacities[{idx}].grade_code is required")
    elif grade_code not in VALID_GRADE_CODES:
        errors.append(
            f"capacities[{idx}].grade_code '{grade_code}' is not valid "
            f"(valid: {sorted(VALID_GRADE_CODES)})"
        )
    try:
        seats = int(cap.get("target_seats", -1))
        if seats < 0:
            errors.append(f"capacities[{idx}].target_seats must be a non-negative integer")
    except (TypeError, ValueError):
        errors.append(f"capacities[{idx}].target_seats must be an integer")
    return errors


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
    session = EnrollmentPeriodWizardSession.objects.create(
        school=school,
        created_by=request.user,
        status=EnrollmentPeriodWizardSession.STATUS_DRAFT,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure session: academic_year + dates + reenroll settings
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    data = request.data
    errors = []

    # academic_year_id — must reference an AcademicYear belonging to this school
    ay_id = (data.get("academic_year_id") or "").strip()
    if not ay_id:
        errors.append("academic_year_id is required")

    # open_date / close_date
    open_date_val, open_err = _parse_date(data.get("open_date"), "open_date")
    if open_err:
        errors.append(open_err)

    close_date_val, close_err = _parse_date(data.get("close_date"), "close_date")
    if close_err:
        errors.append(close_err)

    if open_date_val and close_date_val and close_date_val <= open_date_val:
        errors.append("close_date must be after open_date")

    # reenroll_close_date (optional) — must be within [open_date, close_date]
    reenroll_close_val = None
    raw_rc = data.get("reenroll_close_date", "")
    if raw_rc:
        reenroll_close_val, rc_err = _parse_date(raw_rc, "reenroll_close_date")
        if rc_err:
            errors.append(rc_err)
        elif open_date_val and close_date_val and reenroll_close_val:
            if not (open_date_val <= reenroll_close_val <= close_date_val):
                errors.append("reenroll_close_date must be within [open_date, close_date]")

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    # Resolve AcademicYear — must belong to request school
    ay = AcademicYear.objects.filter(pk=ay_id, school_id=school_id).first()
    if ay is None:
        return Response(
            {"error": "academic_year_id not found for this school"},
            status=status.HTTP_404_NOT_FOUND,
        )

    session.academic_year    = ay
    session.open_date        = str(open_date_val)
    session.close_date       = str(close_date_val)
    session.reenroll_close_date = str(reenroll_close_val) if reenroll_close_val else ""
    session.reenroll_first   = bool(data.get("reenroll_first", False))
    session.status           = EnrollmentPeriodWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id":          str(session.id),
        "status":              session.status,
        "academic_year_id":   str(ay.id),
        "academic_year_name": ay.name,
        "open_date":          session.open_date,
        "close_date":         session.close_date,
        "reenroll_close_date": session.reenroll_close_date or None,
        "reenroll_first":     session.reenroll_first,
    })


# ---------------------------------------------------------------------------
# 3. Set capacities
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_capacities(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == EnrollmentPeriodWizardSession.STATUS_DRAFT:
        return Response(
            {"error": "session must be configured before setting capacities"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw = request.data.get("capacities", [])
    if not raw:
        return Response(
            {"error": "capacities list is required and must not be empty"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    errors = []
    for idx, cap in enumerate(raw):
        errors.extend(_validate_capacity(cap, idx))

    # Batch dedup on grade_code
    seen_codes = set()
    for idx, cap in enumerate(raw):
        code = (cap.get("grade_code") or "").strip()
        if code in seen_codes:
            errors.append(f"capacities: duplicate grade_code '{code}'")
        seen_codes.add(code)

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    # Normalise and store
    session.capacities_config = [
        {
            "grade_code":           (c.get("grade_code") or "").strip(),
            "target_seats":         int(c.get("target_seats", 0)),
            "new_students_allowed": bool(c.get("new_students_allowed", True)),
        }
        for c in raw
    ]
    session.status = EnrollmentPeriodWizardSession.STATUS_CAPACITIES_SET
    session.save()

    return Response({
        "session_id":       str(session.id),
        "status":           session.status,
        "capacities_count": len(session.capacities_config),
    })


# ---------------------------------------------------------------------------
# 4. Commit session
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != EnrollmentPeriodWizardSession.STATUS_CAPACITIES_SET:
        return Response(
            {"error": f"session must be in capacities_set state before commit (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    school = get_object_or_404(School, id=school_id)
    ay = session.academic_year

    with transaction.atomic():
        # Serialize concurrent "create/update enrollment period" operations for this school+year
        list(EnrollmentPeriod.objects.select_for_update().filter(school=school, academic_year=ay))

        ep, ep_created = EnrollmentPeriod.objects.get_or_create(
            school=school,
            academic_year=ay,
            defaults={
                "open_date":          session.open_date,
                "close_date":         session.close_date,
                "reenroll_close_date": session.reenroll_close_date or None,
                "reenroll_first":     session.reenroll_first,
                "is_active":          True,
            },
        )

        if not ep_created:
            # Idempotent update on re-commit
            ep.open_date           = session.open_date
            ep.close_date          = session.close_date
            ep.reenroll_close_date = session.reenroll_close_date or None
            ep.reenroll_first      = session.reenroll_first
            ep.is_active           = True
            ep.save(update_fields=[
                "open_date", "close_date", "reenroll_close_date", "reenroll_first", "is_active",
            ])

        caps_created = 0
        caps_updated = 0
        for c in session.capacities_config:
            _, created = GradeCapacity.objects.update_or_create(
                school=school,
                academic_year=ay,
                grade_code=c["grade_code"],
                defaults={
                    "target_seats":         c["target_seats"],
                    "new_students_allowed": c["new_students_allowed"],
                },
            )
            if created:
                caps_created += 1
            else:
                caps_updated += 1

        result = {
            "enrollment_period_id":  str(ep.pk),
            "academic_year_id":      str(ay.pk),
            "academic_year_name":    ay.name,
            "open_date":             str(ep.open_date),
            "close_date":            str(ep.close_date),
            "reenroll_close_date":   str(ep.reenroll_close_date) if ep.reenroll_close_date else None,
            "reenroll_first":        ep.reenroll_first,
            "created":               ep_created,
            "capacities_created":    caps_created,
            "capacities_updated":    caps_updated,
            "message": (
                f"Enrollment period created for '{ay.name}' with {caps_created + caps_updated} grade(s)."
                if ep_created
                else f"Enrollment period updated for '{ay.name}'; "
                     f"{caps_created} new grade(s), {caps_updated} updated."
            ),
        }
        session.commit_result = result
        session.status        = EnrollmentPeriodWizardSession.STATUS_COMMITTED
        session.save()

    # Audit (non-fatal)
    try:
        AuditLog.objects.create(
            user_id=request.user.id,
            action="enrollment_period.commit",
            model="EnrollmentPeriod",
            object_id=str(ep.pk),
            metadata={"academic_year_id": str(ay.pk), "school_id": str(school.pk)},
        )
    except Exception as exc:
        logger.warning("enrollment_period.commit audit log skipped: %s", exc)

    return Response({"session_id": str(session.id), "status": session.status, "result": result})


# ---------------------------------------------------------------------------
# 5. Verify session
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != EnrollmentPeriodWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": "session must be committed before verify"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    school = get_object_or_404(School, id=school_id)
    ay     = session.academic_year

    period_exists  = EnrollmentPeriod.objects.filter(school=school, academic_year=ay).exists()
    capacity_count = GradeCapacity.objects.filter(school=school, academic_year=ay).count()

    session.status = EnrollmentPeriodWizardSession.STATUS_VERIFIED
    session.save(update_fields=["status"])

    return Response({
        "session_id":       str(session.id),
        "status":           session.status,
        "period_exists":    period_exists,
        "capacity_count":   capacity_count,
        "academic_year_id": str(ay.pk),
        "academic_year_name": ay.name,
    })
