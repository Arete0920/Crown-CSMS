from django.http import JsonResponse
from django.conf import settings
import os


def health(request):
    build_sha = os.getenv("BUILD_SHA", "local-dev")
    return JsonResponse({
        "ok": True,
        "status": "ok",
        "build_sha": build_sha,
    })


def health_version(request):
    """Detailed version info for deployment verification."""
    return JsonResponse({
        "build_sha": BUILD_SHA or "unknown",
        "build_time": BUILD_TIME or "unknown",
        "env": os.environ.get("CROWN_ENV", "unknown"),
        "debug": getattr(settings, "DEBUG", False),
    })
