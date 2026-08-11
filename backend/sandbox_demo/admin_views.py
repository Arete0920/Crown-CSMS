from dataclasses import asdict

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .admin_operations import SandboxAdminError, resolve_admin_demo_workflow, serialize_admin_state


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sandbox_admin_state(request):
    try:
        return Response(asdict(serialize_admin_state(request.user)))
    except SandboxAdminError as exc:
        return Response({"detail": str(exc)}, status=403)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sandbox_admin_resolve(request):
    try:
        return Response(resolve_admin_demo_workflow(request.user))
    except SandboxAdminError as exc:
        return Response({"detail": str(exc)}, status=400)
