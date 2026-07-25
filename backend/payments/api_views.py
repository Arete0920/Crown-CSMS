from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from payments.hold import payment_hold_response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    return payment_hold_response()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_intent_status(request, intent_id: str):
    return payment_hold_response()
