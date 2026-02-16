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
