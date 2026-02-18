from django.conf import settings
from django.http import JsonResponse, HttpResponse

class TenantHeaderRequiredMiddleware:
    """
    Requires X-School-Id header for all /api/v1/* routes except exemptions.
    Disabled when settings.TENANT_HEADER_REQUIRED is False (e.g. in tests).
    """

    API_PREFIX = "/api/v1/"
    EXEMPT_PREFIXES = (
        "/api/v1/health",
        "/api/v1/auth",
        "/api/v1/system/health",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "TENANT_HEADER_REQUIRED", True):
            return self.get_response(request)
        
        path = request.path or ""
        
        # Always allow OPTIONS requests (CORS preflight) to pass through
        # so CorsMiddleware can add proper CORS headers
        if request.method == "OPTIONS":
            return self.get_response(request)
        
        if path.startswith(self.API_PREFIX) and not path.startswith(self.EXEMPT_PREFIXES):
            school_id = request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
            if not school_id:
                return JsonResponse(
                    {"detail": "Missing required header: X-School-Id"},
                    status=400
                )
        return self.get_response(request)
