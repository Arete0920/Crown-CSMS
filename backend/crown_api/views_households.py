from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from crown_api.models import Household
from crown_api.serializers_households import HouseholdReadSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def households_list(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)

    qs = Household.objects.order_by("household_name")
    if not access.is_staff:
        qs = qs.filter(id__in=access.household_ids)

    qs = qs.prefetch_related("members__person", "students__person").order_by(
        "household_name"
    )
    return Response(HouseholdReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_detail(request, household_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)

    if not access.is_staff and household_id not in access.household_ids:
        raise Http404()

    qs = Household.objects.prefetch_related("members__person", "students__person")
    if not access.is_staff:
        qs = qs.filter(id__in=access.household_ids)

    obj = get_object_or_404(qs, id=household_id)
    return Response(HouseholdReadSerializer(obj).data)
