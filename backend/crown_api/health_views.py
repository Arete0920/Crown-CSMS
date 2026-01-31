from django.http import JsonResponse
from django.conf import settings
import os

try:
    from crown_api.build_info import BUILD_SHA, BUILD_TIME
except Exception:
    BUILD_SHA = "unknown"
    BUILD_TIME = "unknown"


def health(request):
    return JsonResponse({
        "ok": True,
        "status": "ok",
        "build_sha": (BUILD_SHA or "unknown")[:7],
    })


def health_version(request):
    """Detailed version info for deployment verification."""
    return JsonResponse({
        "build_sha": BUILD_SHA or "unknown",
        "build_time": BUILD_TIME or "unknown",
        "env": os.environ.get("CROWN_ENV", "unknown"),
        "debug": getattr(settings, "DEBUG", False),
    })
