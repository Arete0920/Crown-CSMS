from django.conf import settings
from django.http import HttpResponse, JsonResponse
import uuid
from core.models import School
from core.tenant_models import set_current_school, clear_current_school

class TenantHeaderRequiredMiddleware:
    """
    Enforces tenant safety for /api/v1/* by requiring X-School-Id.
    - Exempts auth + health endpoints.
    - Lets OPTIONS pass through so CORS middleware can add headers.
    - Validates X-School-Id is a UUID and that the School exists.
    - Attaches request.school_id and request.school for downstream use.
    """

    EXEMPT_PREFIXES = (
        "/api/v1/health",
        "/api/v1/system/health",
        "/api/v1/auth",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Allow CORS preflight to flow to CorsMiddleware
            if request.method == "OPTIONS":
                return self.get_response(request)

            # If enforcement disabled, just pass through
            if not getattr(settings, "TENANT_HEADER_REQUIRED", True):
                return self.get_response(request)

            path = request.path or ""

            # Only enforce /api/v1/*
            if not path.startswith("/api/v1/"):
                return self.get_response(request)

            # Exempt prefixes
            for prefix in self.EXEMPT_PREFIXES:
                if path.startswith(prefix):
                    return self.get_response(request)

            school_id_raw = request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
            if not school_id_raw:
                return JsonResponse({"detail": "Missing required header: X-School-Id"}, status=400)

            # Validate UUID
            try:
                school_uuid = uuid.UUID(str(school_id_raw))
            except Exception:
                return JsonResponse({"detail": "Invalid X-School-Id (must be UUID)"}, status=400)

            # Validate School exists
            school = School.objects.filter(id=school_uuid).only("id").first()
            if school is None:
                return JsonResponse({"detail": "Unknown X-School-Id"}, status=404)

            # Attach for downstream consumption
            request.school_id = str(school_uuid)
            request.school = school
            set_current_school(school)

            return self.get_response(request)
        finally:
            # Always clear tenant context after request (even on exceptions)
            clear_current_school()
