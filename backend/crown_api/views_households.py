from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.models import Household
from crown_api.serializers_households import HouseholdReadSerializer


def _staff_only(request) -> bool:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False
    return bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def households_list(request):
    if not _staff_only(request):
        return Response({"detail": "Not authorized"}, status=403)

    qs = (
        Household.objects.all()
        .prefetch_related("members__person", "students__person")
        .order_by("household_name")
    )
    return Response(HouseholdReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_detail(request, household_id):
    if not _staff_only(request):
        return Response({"detail": "Not authorized"}, status=403)

    obj = get_object_or_404(
        Household.objects.prefetch_related("members__person", "students__person"),
        id=household_id,
    )
    return Response(HouseholdReadSerializer(obj).data)
