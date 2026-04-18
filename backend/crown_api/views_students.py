from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from core.models import Student
from crown_api.serializers_students import StudentReadSerializer


def _guardian_family_id(user):
    guardian = getattr(user, "guardian", None)
    return getattr(guardian, "family_id", None)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def students_list(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)
    qs = Student.objects.select_related("school", "family")

    if not access.is_staff:
        family_id = _guardian_family_id(request.user)
        if family_id is None:
            return Response([], status=200)
        qs = qs.filter(family_id=family_id)

    qs = qs.order_by("last_name", "first_name")
    return Response(StudentReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_detail(request, student_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)
    qs = Student.objects.select_related("school", "family")

    if not access.is_staff:
        family_id = _guardian_family_id(request.user)
        if family_id is None:
            return Response({"detail": "Not found."}, status=404)
        qs = qs.filter(family_id=family_id)

    obj = get_object_or_404(qs, id=student_id)
    return Response(StudentReadSerializer(obj).data)
