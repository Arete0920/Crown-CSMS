from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from crown_api.access_households import resolve_person_for_user, resolve_household_access
from crown_api.models import AttendanceRecord, GradeRecord, HouseholdMember
from core.models import Student
from crown_api.models_households import GUARDIAN_ROLES
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_academics import AttendanceRecordReadSerializer, GradeRecordReadSerializer


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
@permission_classes([AllowAny])
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
    POST /api/v1/academics/sections/<section_id>/attendance/
    Teacher submits attendance for a section for today (or a provided date).

    Body:
      {
        "date": "YYYY-MM-DD",  (optional; defaults to today)
        "items": [
          {"student_id": "<uuid>", "status": "present|absent|tardy|PRESENT|ABSENT|TARDY"},
          ...
        ]
      }

    Upserts AttendanceRecord rows keyed by (student_id, course_id, date).
    Returns: {"ok": true, "date": "YYYY-MM-DD", "created": N, "updated": N}
    """
    payload = request.data or {}
    items = payload.get("items") or []
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

    # Resolve section to verify it exists (section_id in URL is from academics.models.Section)
    from academics.models import Section
    get_object_or_404(Section, id=section_id)
    # NOTE: we do NOT use section.course_id here — AttendanceRecord.course targets a
    # different Course model (crown_api.models_academics_core.Course) than academics.models.Course.
    # Attendance is recorded per student+date only; course is left null (nullable FK).

    created = 0
    updated = 0

    for row in items:
        sid = row.get("student_id")
        status = row.get("status")
        if not sid or not status:
            return Response(
                {"ok": False, "error": "each item requires student_id + status"},
                status=400,
            )

        try:
            obj, was_created = AttendanceRecord.objects.get_or_create(
                student_id=sid,
                date=day,
                defaults={"status": status},
            )
        except Exception as exc:
            return Response(
                {"ok": False, "error": f"could not save attendance for student_id={sid}: {exc}"},
                status=400,
            )

        if was_created:
            created += 1
        else:
            obj.status = status
            obj.save(update_fields=["status", "updated_at"])
            updated += 1

    return Response({"ok": True, "date": str(day), "created": created, "updated": updated})


@api_view(["GET"])
@permission_classes([AllowAny])
def student_grades_list(request, student_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    _assert_student_in_scope_or_404(request, student_id)

    qs = GradeRecord.objects.filter(student_id=student_id).select_related("course")
    return Response(GradeRecordReadSerializer(qs, many=True).data)
