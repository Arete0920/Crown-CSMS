from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import health_check, get_connector_status


@api_view(["GET"])
@permission_classes([AllowAny])
def connectors_health(request):
    return Response(health_check())


@api_view(["GET"])
@permission_classes([AllowAny])
def connectors_status(request):
    return Response(get_connector_status())
