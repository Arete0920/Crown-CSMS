import os

from django.http import JsonResponse


def health(request):
    build_sha = (
        os.environ.get("BUILD_SHA")
        or os.environ.get("GITHUB_SHA")
        or os.environ.get("WEBSITE_RUN_FROM_PACKAGE")
        or "unknown"
    )
    return JsonResponse({"ok": True, "status": "ok", "build_sha": build_sha})
