from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_person_for_user, resolve_household_access
from crown_api.models import AttendanceRecord, GradeRecord, HouseholdMember
from core.models import Student, UserRole
from crown_api.models_households import GUARDIAN_ROLES
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_academics import AttendanceRecordReadSerializer, GradeRecordReadSerializer
from households.scoping import get_request_school_id


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
    school_id = get_request_school_id(request, required=False)
    if school_id:
        roles = set(
            UserRole.objects.filter(user_id=request.user.id, school_id=school_id)
            .values_list("role_code", flat=True)
        )
        allowed = {"TEACHER", "ADMIN", "HEAD_OF_SCHOOL"}
        if not roles.intersection(allowed):
            return Response({"detail": "Forbidden: requires TEACHER, ADMIN, or HEAD_OF_SCHOOL role."}, status=403)

    payload = request.data or {}

    # Accept both "items" (existing callers) and "records" (new convention)
    items = payload.get("items") or payload.get("records") or []
    if not isinstance(items, list) or len(items) == 0:
        return Response({"ok": False, "error": "items[] required (list of {student_id, status})"}, status=400)

    # Resolve date
    raw_date = payload.get("date")
    if raw_date:
        try:
            day = timezone.datetime.fromisoformat(str(raw_date)).date()
        except Exception:
            return Response({"ok": False, "error": "invalid date — use YYYY-MM-DD"}, status=400)
    else:
        day = timezone.localdate()

    # Resolve section to verify it exists
    from academics.models import Section
    get_object_or_404(Section, id=section_id)

    VALID_STATUSES = {"PRESENT", "ABSENT", "TARDY", "EXCUSED"}
    created = 0
    updated = 0

    for row in items:
        sid = row.get("student_id")
        raw_status = str(row.get("status") or "").upper().strip()
        if not sid:
            return Response({"ok": False, "error": "each item requires student_id"}, status=400)
        if raw_status not in VALID_STATUSES:
            raw_status = "PRESENT"

        try:
            obj, was_created = AttendanceRecord.objects.update_or_create(
                student_id=sid,
                course=None,
                date=day,
                defaults={"status": raw_status},
            )
        except Exception as exc:
            return Response(
                {"ok": False, "error": f"could not save attendance for student_id={sid}: {exc}"},
                status=400,
            )

        if was_created:
            created += 1
        else:
            updated += 1

    return Response({"ok": True, "date": str(day), "section_id": str(section_id), "created": created, "updated": updated})


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
