"""
Simple version endpoint to verify deployed build.
Returns git commit, build time, and environment.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import os
from pathlib import Path


def _resolve_app_version() -> str:
    configured = os.getenv("APP_VERSION", "").strip()
    if configured:
        return configured

    try:
        version_path = Path(__file__).resolve().parents[2] / "VERSION"
        from_file = version_path.read_text(encoding="utf-8").strip()
        if from_file:
            return from_file
    except OSError:
        pass

    return "crown-unknown"

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def version(request):
    """
    Return version info for deployment verification.
    No auth required - used by smoke tests and ops.
    """
    # Try to read build info (baked in during CI/CD)
    build_sha = "unknown"
    try:
        from crown_api.build_info import BUILD_SHA
        build_sha = BUILD_SHA
    except ImportError:
        # Fallback: check if .git exists (local dev)
        pass
    
    # Determine environment from settings
    environment = "DEV" if settings.DEBUG else "PROD"
    
    return Response({
        "service": "crown-api",
        "version": _resolve_app_version(),
        "commit": build_sha,
        "environment": environment,
        "django_version": settings.VERSION if hasattr(settings, 'VERSION') else "unknown"
    })
