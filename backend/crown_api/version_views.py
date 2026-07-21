"""
Lightweight version endpoint for quick deployment verification.
No DB checks, faster than /health.
"""
import os
from pathlib import Path

from django.http import JsonResponse
from django.utils import timezone

# Runtime deployment identity is authoritative. Older images may contain a
# shortened baked fallback, while Azure app settings carry the full immutable
# 40-character release SHA.
try:
    from crown_api.build_info import BUILD_SHA as BAKED_BUILD_SHA
except ImportError:
    BAKED_BUILD_SHA = "unknown"

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


def _resolve_build_sha() -> str:
    """Return the immutable runtime release identity when available."""
    configured = (os.getenv("BUILD_SHA") or os.getenv("GITHUB_SHA") or "").strip()
    if configured:
        return configured

    baked = str(BAKED_BUILD_SHA or "").strip()
    return baked or "unknown"


def version(request):
    """Return public deployment identity without a database check."""
    return JsonResponse(
        {
            "version": _resolve_app_version(),
            "build_sha": _resolve_build_sha(),
            "build_time": BUILD_TIME,
            "server_time": timezone.now().isoformat(),
        }
    )
