from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from governance.microsoft_graph import build_board_delivery_channels


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def governance_dashboard(request):
    """School-board governance dashboard summary."""
    return Response({}, status=status.HTTP_200_OK)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def m365_services_status(request):
    """Return fail-closed Microsoft service readiness booleans for UI/proof checks."""
    school = getattr(request, "school", None)
    school_id = getattr(school, "id", None)

    delivery = build_board_delivery_channels(school_id)
    channels = {
        row.get("channel"): row.get("status") for row in delivery.get("channels", [])
    }

    payload = {
        "outlook": channels.get("email") == "configured",
        "sharepoint": channels.get("sharepoint") == "configured",
        "teams": channels.get("teams") == "configured",
        # Not yet wired in this phase - explicit fail-closed behavior.
        "planner": False,
        "esignature": False,
    }
    return Response(payload, status=status.HTTP_200_OK)
