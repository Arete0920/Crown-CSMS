from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.models import (
    GatewayIntentStatus,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    return Response(
        {
            "ok": False,
            "error": "External payment provider deferred pending vendor coordination.",
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_intent_status(request, intent_id: str):
    return Response(
        {
            "ok": False,
            "error": "External payment provider deferred pending vendor coordination.",
            "intent_id": intent_id,
            "status": GatewayIntentStatus.FAILED,
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
