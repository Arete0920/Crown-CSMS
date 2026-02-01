"""
Lightweight version endpoint for quick deployment verification.
No DB checks, faster than /health.
"""
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
        "version": "1.0.0",
        "build_sha": BUILD_SHA,
        "build_time": BUILD_TIME,
        "server_time": timezone.now().isoformat(),
    })
