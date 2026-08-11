from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .parent_daily import SandboxParentDailyError, parent_daily_state


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sandbox_parent_daily(request):
    try:
        return Response(parent_daily_state(request.user))
    except SandboxParentDailyError as exc:
        return Response({"detail": str(exc)}, status=403)
