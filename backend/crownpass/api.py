from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from households.scoping import get_request_school_id

from .services import list_family_tickets


@extend_schema(
    responses=OpenApiTypes.OBJECT,
    description=(
        "Return CrownPass tickets owned by the authenticated user within the "
        "asserted school tenant. Raw admission credentials are intentionally "
        "excluded from this compatibility endpoint."
    ),
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tickets(request):
    school_id = get_request_school_id(request, required=True)
    tickets = list_family_tickets(school_id=school_id, user=request.user)
    return Response({
        "count": len(tickets),
        "tickets": tickets,
    })
