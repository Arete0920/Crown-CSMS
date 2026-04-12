import logging

from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_person_for_user, resolve_household_access
from crown_api.models import AttendanceRecord, GradeRecord, HouseholdMember
from core.models import Student, UserRole
from crown_api.models_households import GUARDIAN_ROLES
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_academics import (
    AttendanceRecordReadSerializer,
    AttendanceSubmitRequestSerializer,
    AttendanceSubmitResponseSerializer,
    GradeRecordReadSerializer,
)
from households.scoping import get_request_school_id


logger = logging.getLogger(__name__)

_ATTENDANCE_ALLOWED_ROLES = {"TEACHER", "ADMIN", "HEAD_OF_SCHOOL"}
_VALID_ATTENDANCE_STATUSES = {"PRESENT", "ABSENT", "TARDY", "EXCUSED"}


def _guardian_household_ids_for_user(request) -> set:
    access = resolve_household_access(request)
    if access.is_staff:
        return set()

    person = resolve_person_for_user(getattr(request, "user", None))
    if not person:
        return set()

    return set(
        HouseholdMember.objects.filter(person=person, role__in=GUARDIAN_ROLES).values_list(
            "household_id", flat=True
        )
    )


def _assert_student_in_scope_or_404(request, student_id) -> None:
    # Enforce household-based access control
    get_core_student_or_404_for_request(request=request, student_id=student_id)


@extend_schema(tags=["academics"], responses={200: AttendanceRecordReadSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_list(request, student_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    _assert_student_in_scope_or_404(request, student_id)

    qs = AttendanceRecord.objects.filter(student_id=student_id).select_related("course")
    return Response(AttendanceRecordReadSerializer(qs, many=True).data)


# --- Lane 3: Teacher Attendance WRITE endpoint ---

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated


def _resolve_attendance_items(payload):
    items = payload.get("items") or payload.get("records") or []
    if not isinstance(items, list) or not items:
        raise ValueError("items[] required (list of {student_id, status})")
    return items


def _resolve_attendance_day(raw_date):
    if not raw_date:
        return timezone.localdate()
    try:
        return timezone.datetime.fromisoformat(str(raw_date)).date()
    except Exception as exc:
        raise ValueError("invalid date — use YYYY-MM-DD") from exc


def _upsert_attendance_row(*, sid, raw_status, school_id, day):
    status_code = raw_status if raw_status in _VALID_ATTENDANCE_STATUSES else "PRESENT"
    get_object_or_404(Student, id=sid, school_id=school_id)
    _, was_created = AttendanceRecord.objects.update_or_create(
        student_id=sid,
        course=None,
        date=day,
        defaults={"status": status_code},
    )
    return was_created


@extend_schema(
    tags=["academics"],
    request=AttendanceSubmitRequestSerializer,
    responses={200: AttendanceSubmitResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def section_attendance_submit(request, section_id):
    """
    ATTENDANCE_HARDENING_V2
    POST /api/v1/academics/sections/<section_id>/attendance/

    Idempotent: update_or_create keyed by (student_id, course=None, date).
    RBAC: TEACHER / ADMIN / HEAD_OF_SCHOOL only.

    Body:
      {
        "date": "YYYY-MM-DD",          (optional; defaults to today)
        "items": [                      (also accepts "records" key)
          {"student_id": "<uuid>", "status": "PRESENT|ABSENT|TARDY|EXCUSED"},
          ...
        ]
      }

    Returns: {"ok": true, "date": "YYYY-MM-DD", "section_id": "...", "created": N, "updated": N}
    """
    # --- RBAC ---
    school_id = get_request_school_id(request, required=True)
    roles = set(
        UserRole.objects.filter(user_id=request.user.id, school_id=school_id)
        .values_list("role_code", flat=True)
    )
    if not roles.intersection(_ATTENDANCE_ALLOWED_ROLES):
        return Response({"detail": "Forbidden: requires TEACHER, ADMIN, or HEAD_OF_SCHOOL role."}, status=403)

    payload = request.data or {}
    try:
        items = _resolve_attendance_items(payload)
        day = _resolve_attendance_day(payload.get("date"))
    except ValueError as exc:
        return Response({"ok": False, "error": str(exc)}, status=400)

    # Resolve section to verify it exists and belongs to this school
    from academics.models import Section
    get_object_or_404(Section, id=section_id, school_id=school_id)

    created = 0
    updated = 0

    for row in items:
        sid = row.get("student_id")
        raw_status = str(row.get("status") or "").upper().strip()
        if not sid:
            return Response({"ok": False, "error": "each item requires student_id"}, status=400)

        try:
            was_created = _upsert_attendance_row(
                sid=sid,
                raw_status=raw_status,
                school_id=school_id,
                day=day,
            )
        except Exception:
            logger.exception("section_attendance_submit: failed to save attendance row", extra={"student_id": sid, "section_id": str(section_id)})
            return Response(
                {"ok": False, "error": f"could not save attendance for student_id={sid}"},
                status=400,
            )

        if was_created:
            created += 1
        else:
            updated += 1

    return Response({"ok": True, "date": str(day), "section_id": str(section_id), "created": created, "updated": updated})


@extend_schema(tags=["academics"], responses={200: GradeRecordReadSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_grades_list(request, student_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    _assert_student_in_scope_or_404(request, student_id)

    qs = GradeRecord.objects.filter(student_id=student_id).select_related("course")
    return Response(GradeRecordReadSerializer(qs, many=True).data)
