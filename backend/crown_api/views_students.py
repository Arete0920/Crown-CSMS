from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from crown_api.access_households import resolve_person_for_user, resolve_household_access
from crown_api.models import HouseholdMember, Student
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
@permission_classes([AllowAny])
def students_list(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)

    qs = Student.objects.select_related("person", "household").select_related(
        "profile"
    )

    if not access.is_staff:
        household_ids = _guardian_household_ids_for_user(request)
        qs = qs.filter(household_id__in=household_ids)

    qs = qs.order_by("person__last_name", "person__first_name")
    return Response(StudentReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def student_detail(request, student_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)

    qs = Student.objects.select_related("person", "household").select_related("profile")

    if not access.is_staff:
        household_ids = _guardian_household_ids_for_user(request)

        # No existence leak: if student isn't in-scope, return 404
        if not qs.filter(id=student_id, household_id__in=household_ids).exists():
            raise Http404()

        qs = qs.filter(household_id__in=household_ids)

    obj = get_object_or_404(qs, id=student_id)
    return Response(StudentReadSerializer(obj).data)
