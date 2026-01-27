from django.http import JsonResponse

try:
    from crown_api.build_info import BUILD_SHA
except Exception:
    BUILD_SHA = "unknown"


def health(request):
    return JsonResponse({
        "ok": True,
        "status": "ok",
        "build_sha": (BUILD_SHA or "unknown")[:7],
    })
