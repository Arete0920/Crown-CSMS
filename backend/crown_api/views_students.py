from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_person_for_user, resolve_household_access
from crown_api.models import HouseholdMember
from core.models import Student
from crown_api.models_households import GUARDIAN_ROLES
from crown_api.serializers_students import StudentReadSerializer


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def students_list(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)

    qs = Student.objects.select_related("school")

    if not access.is_staff:
        # TODO: Implement family-based filtering after core.Student migration
        # core.Student uses family FK, not household
        pass

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

    qs = Student.objects.select_related("school")

    if not access.is_staff:
        # TODO: Implement family-based access control after core.Student migration
        # For now, allow all authenticated users (parent scoping needs family→household link)
        pass

    obj = get_object_or_404(qs, id=student_id)
    return Response(StudentReadSerializer(obj).data)
