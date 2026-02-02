"""
DEV-only ops endpoints for CI automation.
Guarded by X-Dev-Ops-Secret header.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


def _dev_ops_enabled() -> bool:
    # Only allow in DEV; keep this strict.
    return bool(getattr(settings, "DEV_OPS_SECRET", "")) and getattr(settings, "ENVIRONMENT", "dev") == "dev"


def _check_ops_secret(request) -> bool:
    header = request.headers.get("X-Dev-Ops-Secret", "")
    expected = getattr(settings, "DEV_OPS_SECRET", "")
    return bool(expected) and header == expected


@api_view(["POST"])
@permission_classes([AllowAny])
def ensure_ci_user(request):
    """
    DEV-only: Create or reset a CI user account for Golden Path smoke tests.
    Guarded by X-Dev-Ops-Secret header.
    
    Request body:
    {
      "username": "ci-golden@crown-demo.local",
      "password": "strong-password"
    }
    """
    if not _dev_ops_enabled():
        # Hide endpoint existence outside dev
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _check_ops_secret(request):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    username = (request.data or {}).get("username", "")
    password = (request.data or {}).get("password", "")

    if not username or not password:
        return Response({"detail": "username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()

    # For most custom User models this works; if yours uses email as USERNAME_FIELD, this still works
    lookup_field = getattr(User, "USERNAME_FIELD", "username")
    lookup = {lookup_field: username}

    user, created = User.objects.get_or_create(defaults={}, **lookup)

    # Ensure account is usable for Golden Path
    user.is_active = True
    user.is_superuser = True  # Superuser bypasses Director role checks
    if hasattr(user, "is_staff"):
        user.is_staff = True

    user.set_password(password)
    user.save()

    return Response(
        {
            "ok": True,
            "created": created,
            "username": username,
            "user_id": str(user.pk),
        },
        status=status.HTTP_200_OK,
    )
