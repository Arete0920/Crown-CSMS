"""Read-only legacy student endpoints with fail-closed tenant attribution."""

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from crown_api.legacy_household_scope import tenant_household_ids
from crown_api.models import Student
from crown_api.serializers_students import StudentReadSerializer
from households.scoping import get_request_school_id


def _authorized_students(request):
    school_id = get_request_school_id(request, required=True)
    access = resolve_household_access(request)
    # StudentReadSerializer is the crown_api legacy Student contract, not
    # core.Student. That compatibility model has no school ID, so restrict
    # through verified single-school household/family attribution.
    qs = Student.objects.filter(
        household_id__in=tenant_household_ids(school_id)
    ).select_related("person", "household")
    if not access.is_staff:
        qs = qs.filter(household_id__in=access.household_ids)
    return qs


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def students_list(request):
    qs = _authorized_students(request).order_by(
        "person__last_name", "person__first_name", "id"
    )
    return Response(StudentReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_detail(request, student_id):
    student = get_object_or_404(_authorized_students(request), id=student_id)
    return Response(StudentReadSerializer(student).data)
