"""Read-only legacy household endpoints with explicit school attribution."""

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from crown_api.legacy_household_scope import tenant_household_ids
from crown_api.models import Household
from crown_api.serializers_households import HouseholdReadSerializer
from households.scoping import get_request_school_id


def _authorized_households(request):
    # Neither global Django staff status nor a legacy household ID carries
    # school authority. Resolve an active authorized school before querying.
    school_id = get_request_school_id(request, required=True)
    access = resolve_household_access(request)
    qs = Household.objects.filter(id__in=tenant_household_ids(school_id))
    if not access.is_staff:
        qs = qs.filter(id__in=access.household_ids)
    return qs


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def households_list(request):
    qs = (
        _authorized_households(request)
        .prefetch_related("members__person", "students__person")
        .order_by("household_name")
    )
    return Response(HouseholdReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_detail(request, household_id):
    qs = _authorized_households(request).prefetch_related(
        "members__person", "students__person"
    )
    household = get_object_or_404(qs, id=household_id)
    return Response(HouseholdReadSerializer(household).data)
