from dataclasses import asdict

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .finance import SandboxFinanceError, apply_demo_payment, serialize_finance_state


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sandbox_finance_state(request):
    try:
        return Response(asdict(serialize_finance_state(request.user)))
    except SandboxFinanceError as exc:
        return Response({"detail": str(exc)}, status=403)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sandbox_finance_apply_payment(request):
    try:
        return Response(apply_demo_payment(request.user))
    except SandboxFinanceError as exc:
        return Response({"detail": str(exc)}, status=400)
