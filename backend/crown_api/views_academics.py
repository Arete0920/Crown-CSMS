import logging

from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_person_for_user, resolve_household_access
from crown_api.models import AttendanceRecord, GradeRecord, HouseholdMember
from core.models import StudentIdentityLink, UserRole
from crown_api.models_households import GUARDIAN_ROLES
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_academics import AttendanceRecordReadSerializer, GradeRecordReadSerializer
from households.scoping import get_request_school_id


logger = logging.getLogger(__name__)


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


def _verified_attendance_identity(student_id, school_id):
    """Resolve either known student ID form through one same-school VERIFIED bridge.

    The active product currently has callers using both core.Student IDs and
    households.Student IDs. Supporting both is safe only when exactly one
    verified identity link with evidence resolves the supplied UUID. Any
    missing, pending, cross-school, or ambiguous mapping fails closed.
    """
    links = list(
        StudentIdentityLink.objects.select_related("core_student", "compatibility_student")
        .filter(
            school_id=school_id,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school_id=school_id,
            compatibility_student__school_id=school_id,
        )
        .exclude(evidence_reference="")
        .filter(
            Q(core_student_id=student_id) | Q(compatibility_student_id=student_id)
        )[:2]
    )
    if len(links) != 1:
        raise Http404()
    link = links[0]
    return link.core_student, link.compatibility_student


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_list(request, student_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    _assert_student_in_scope_or_404(request, student_id)

    qs = AttendanceRecord.objects.filter(student_id=student_id).select_related(
        "course", "section"
    )
    return Response(AttendanceRecordReadSerializer(qs, many=True).data)


# --- Lane 3: Teacher Attendance WRITE endpoint ---

from django.utils import timezone


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def section_attendance_submit(request, section_id):
    """
    POST /api/v1/academics/sections/<section_id>/attendance/

    Canonical persistence is keyed by (core student, academics section, date).
    The submitted student UUID may be either side of the verified identity
    bridge for compatibility with current callers, but it must resolve to
    exactly one same-school VERIFIED StudentIdentityLink with evidence and the
    compatibility student must be enrolled in the submitted section.

    RBAC: TEACHER (assigned section), REGISTRAR, or HEAD_OF_SCHOOL.
    """
    school_id = get_request_school_id(request, required=True)
    roles = set(
        UserRole.objects.filter(user_id=request.user.id, school_id=school_id)
        .values_list("role_code", flat=True)
    )
    allowed = {"TEACHER", "REGISTRAR", "HEAD_OF_SCHOOL"}
    if not roles.intersection(allowed):
        return Response(
            {"detail": "Forbidden: requires TEACHER, REGISTRAR, or HEAD_OF_SCHOOL role."},
            status=403,
        )

    from academics.models import Enrollment, Section, TeacherAssignment

    section = get_object_or_404(Section, id=section_id, school_id=school_id)

    is_admin = bool(roles.intersection({"REGISTRAR", "HEAD_OF_SCHOOL"}))
    if "TEACHER" in roles and not is_admin:
        teacher_assigned = False
        staff_id = getattr(request.user, "staff_id", None)
        if staff_id:
            teacher_assigned = TeacherAssignment.objects.filter(
                school_id=school_id,
                section_id=section.id,
                staff_id=staff_id,
            ).exists()

        if not teacher_assigned and getattr(section, "teacher_id", None):
            teacher_assigned = str(section.teacher_id) == str(request.user.id)

        if not teacher_assigned:
            return Response(
                {"detail": "Forbidden: assigned teacher required for this section."},
                status=403,
            )

    payload = request.data or {}
    items = payload.get("items") or payload.get("records") or []
    if not isinstance(items, list) or len(items) == 0:
        return Response(
            {"ok": False, "error": "items[] required (list of {student_id, status})"},
            status=400,
        )

    raw_date = payload.get("date")
    if raw_date:
        try:
            day = timezone.datetime.fromisoformat(str(raw_date)).date()
        except Exception:
            return Response(
                {"ok": False, "error": "invalid date — use YYYY-MM-DD"},
                status=400,
            )
    else:
        day = timezone.localdate()

    valid_statuses = {"PRESENT", "ABSENT", "TARDY", "EXCUSED"}
    prepared = []

    # Validate the entire request before writing anything so one invalid row
    # cannot leave a partially persisted attendance submission.
    for row in items:
        if not isinstance(row, dict):
            return Response(
                {"ok": False, "error": "each item must be an object"}, status=400
            )
        sid = row.get("student_id")
        raw_status = str(row.get("status") or "").upper().strip()
        if not sid:
            return Response(
                {"ok": False, "error": "each item requires student_id"}, status=400
            )
        if raw_status not in valid_statuses:
            return Response(
                {"ok": False, "error": f"invalid attendance status for student_id={sid}"},
                status=400,
            )

        core_student, compatibility_student = _verified_attendance_identity(
            sid, school_id
        )
        if not Enrollment.objects.filter(
            school_id=school_id,
            section_id=section.id,
            student_id=compatibility_student.id,
        ).exists():
            raise Http404()

        prepared.append((core_student, raw_status))

    created = 0
    updated = 0
    try:
        with transaction.atomic():
            for core_student, raw_status in prepared:
                _, was_created = AttendanceRecord.objects.update_or_create(
                    student=core_student,
                    section=section,
                    date=day,
                    defaults={"status": raw_status},
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
    except Exception:
        logger.exception(
            "section_attendance_submit: failed to save attendance submission",
            extra={"section_id": str(section_id)},
        )
        return Response(
            {"ok": False, "error": "could not save attendance submission"},
            status=400,
        )

    return Response(
        {
            "ok": True,
            "date": str(day),
            "section_id": str(section_id),
            "created": created,
            "updated": updated,
        }
    )


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
