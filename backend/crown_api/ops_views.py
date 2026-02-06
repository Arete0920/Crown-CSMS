"""
DEV-only ops endpoints for CI automation.
Guarded by X-Admin-Ops-Secret header.
"""
from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import School


def _dev_ops_enabled() -> bool:
    # Only allow in DEV; keep this strict.
    return bool(getattr(settings, "DEV_OPS_SECRET", "")) and getattr(settings, "ENVIRONMENT", "dev") == "dev"


def _check_ops_secret(request) -> bool:
    header = request.headers.get("X-Admin-Ops-Secret", "") or request.META.get("HTTP_X_ADMIN_OPS_SECRET", "")
    expected = getattr(settings, "DEV_OPS_SECRET", "")
    return bool(expected) and header == expected


@api_view(["POST"])
@permission_classes([AllowAny])
def ensure_ci_user(request):
    """
    DEV-only: Create or reset a CI user account for Golden Path smoke tests.
        Guarded by X-Admin-Ops-Secret header.
    
    Request body:
    {
            "username": "ci-golden@crown-demo.local",
            "password": "strong-password",
            "school_id": "<uuid>"
    }
    """
    if not _dev_ops_enabled():
        # Hide endpoint existence outside dev
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _check_ops_secret(request):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    payload = request.data or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    school_id_raw = (payload.get("school_id") or "").strip()

    if not username or not password or not school_id_raw:
        return Response(
            {"detail": "username, password, and school_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        school_id = UUID(school_id_raw)
    except Exception:
        return Response({"detail": "school_id must be a valid UUID"}, status=status.HTTP_400_BAD_REQUEST)

    school = School.objects.filter(id=school_id).first()
    if school is None:
        return Response({"detail": "School not found"}, status=status.HTTP_404_NOT_FOUND)

    User = get_user_model()

    # For most custom User models this works; if yours uses email as USERNAME_FIELD, this still works
    lookup_field = getattr(User, "USERNAME_FIELD", "username")
    lookup = {lookup_field: username}

    user, created = User.objects.get_or_create(defaults={}, **lookup)

    # Ensure account is usable for Golden Path
    user.is_active = True
    if hasattr(user, "is_staff"):
        user.is_staff = True

    user.set_password(password)
    if hasattr(user, "school_id"):
        user.school_id = school_id
    if hasattr(user, "school"):
        user.school = school
    user.save()

    return Response(
        {
            "ok": True,
            "created": created,
            "username": username,
            "school_id": str(school_id),
            "user_id": str(user.pk),
        },
        status=status.HTTP_200_OK,
    )
