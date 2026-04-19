"""
Lightweight version endpoint for quick deployment verification.
No DB checks, faster than /health.
"""
import os
from pathlib import Path

from django.http import JsonResponse
from django.utils import timezone

# Import build artifacts if available
try:
    from crown_api.build_info import BUILD_SHA
except ImportError:
    BUILD_SHA = "unknown"

try:
    from crown_api.build_info import BUILD_TIME
except ImportError:
    BUILD_TIME = None


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


def version(request):
    """
    GET /version/
    Returns version info without DB checks.
    
    Response:
    {
        "version": "1.0.0",
        "build_sha": "94830992...",
        "build_time": "2026-02-01T12:00:00Z",
        "server_time": "2026-02-01T12:05:30Z"
    }
    """
    return JsonResponse({
        "version": _resolve_app_version(),
        "build_sha": BUILD_SHA,
        "build_time": BUILD_TIME,
        "server_time": timezone.now().isoformat(),
    })
