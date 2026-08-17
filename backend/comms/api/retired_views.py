from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


_RETIRED = {
    "detail": (
        "Legacy internal Communications mutation is retired. "
        "Use the governed Microsoft 365/outbox communication workflow."
    )
}


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retired_write(request, *args, **kwargs):
    return Response(_RETIRED, status=status.HTTP_410_GONE)
