"""
DEV-only ops endpoints for CI automation.
Guarded by X-Admin-Ops-Secret header.
"""
from __future__ import annotations

import os
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

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
    DEV-only: Idempotently ensure CI smoke user exists and return JWT.
    Reads credentials from Azure App Service settings (CI_SMOKE_*).
    Guarded by X-Admin-Ops-Secret header.
    
    Returns JWT for immediate use in smoke tests.
    """
    if not _dev_ops_enabled():
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _check_ops_secret(request):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    # Read from server-side env vars (Azure App Service settings)
    username = os.getenv("CI_SMOKE_USERNAME", "").strip()
    password = os.getenv("CI_SMOKE_PASSWORD", "").strip()
    school_id_raw = os.getenv("CI_SMOKE_SCHOOL_ID", "").strip()

    if not username or not password or not school_id_raw:
        return Response(
            {"detail": "Server misconfigured: missing CI_SMOKE_USERNAME, CI_SMOKE_PASSWORD, or CI_SMOKE_SCHOOL_ID"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        school_id = UUID(school_id_raw)
    except Exception:
        return Response(
            {"detail": "Server misconfigured: CI_SMOKE_SCHOOL_ID must be valid UUID"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    school = School.objects.filter(id=school_id).first()
    if school is None:
        return Response(
            {"detail": f"School {school_id} not found"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    User = get_user_model()
    lookup_field = getattr(User, "USERNAME_FIELD", "username")
    lookup = {lookup_field: username}

    user, created = User.objects.get_or_create(defaults={}, **lookup)

    # Ensure account is usable for smoke tests
    user.is_active = True
    if hasattr(user, "is_staff"):
        user.is_staff = True

    # Idempotent password reset (matches Azure setting)
    user.set_password(password)
    
    # Bind tenant context
    if hasattr(user, "school_id"):
        user.school_id = school_id
    if hasattr(user, "school"):
        user.school = school
    user.save()

    # Generate JWT
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response(
        {
            "ok": True,
            "created": created,
            "username": username,
            "school_id": str(school_id),
            "access": access_token,
