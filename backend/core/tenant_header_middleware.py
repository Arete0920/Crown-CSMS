# backend/core/tenant_header_middleware.py
from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse

from core.models import School
from core.tenant_models import set_current_school, clear_current_school
from crown_api.tenant import resolve_tenant_school_id


class TenantHeaderRequiredMiddleware:
    """
    Enforces tenant resolution for /api/* calls.

    Policy (in priority order):
    1. X-School-Id header  used when present (primary)
    2. Authenticated user.school_id  fallback for session/JWT users without a header
    3. Missing tenant  400

    IMPORTANT: This middleware MUST run after AuthenticationMiddleware and
    JwtAuthMiddleware so request.user is populated and the user.school_id
    fallback path works correctly.

    Exempted paths: /api/auth/*, /api/v1/auth/*, /api/health/*, /api/v1/health/*,
    /api/integrity/*, /api/schema/*, /api/docs/*

    Attaches request.school (School instance) and request.school_id (str UUID)
    for downstream view usage, and sets the thread-local tenant context so audit
    and scoping utilities pick up the right school.
    """

    EXEMPT_PREFIXES = (
        "/api/health",
        "/api/v1/health",
        "/api/v1/system/health",
        "/api/integrity",
        "/api/v1/integrity",
        "/api/ops",
        "/api/system/",
        "/api/auth",
        "/api/v1/auth",
        "/api/v1/sandbox",
        "/api/sandbox",
        "/api/billing/",
        "/api/director/",
        "/api/v1/gradebook/",
        "/api/help",
        "/api/v1/help",
        "/api/solomon",
        "/api/v1/solomon",
        "/api/dev/token",  # dev token endpoint returns school_id  no tenant context needed
        "/api/payments/webhooks/",
        "/api/v1/payments/webhooks/",
        "/api/schema",
        "/api/docs",
        "/api/director/force_seed_user",  # dev-only admin utility; predates tenant scoping
        "/api/v1/admissions/submit",
        "/api/admissions/submit",
        "/api/v1/admissions/public-config",
        "/api/admissions/public-config",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # CORS preflight  pass through so CORS middleware adds headers
            if request.method == "OPTIONS":
                return self.get_response(request)

            # Tenant enforcement can be disabled in test/dev via env flag
            if not getattr(settings, "TENANT_HEADER_REQUIRED", True):
                return self.get_response(request)

            path = getattr(request, "path", "") or ""
            normalized_path = path.rstrip("/") or "/"

            # Only enforce on /api/* paths
            if not normalized_path.startswith("/api/"):
                return self.get_response(request)

            # Exempt auth, health, schema, docs
            for prefix in self.EXEMPT_PREFIXES:
                if normalized_path.startswith(prefix):
                    # Preserve header validation semantics when callers explicitly
                    # provide X-School-Id on exempt routes.
                    resolved = resolve_tenant_school_id(request)
                    if resolved.source == "header_invalid":
                        return JsonResponse(
                            {
                                "detail": "Invalid X-School-Id (must be UUID).",
                                "code": "invalid_tenant_header",
                            },
                            status=400,
                        )
                    return self.get_response(request)

            # Resolve tenant: header wins over user.school_id fallback.
            # resolve_tenant_school_id() handles both paths since we now run
            # after AuthenticationMiddleware (request.user is populated).
            resolved = resolve_tenant_school_id(request)
            school_id = resolved.school_id

            if resolved.source == "header_invalid":
                return JsonResponse(
                    {
                        "detail": "Invalid X-School-Id (must be UUID).",
                        "code": "invalid_tenant_header",
                    },
                    status=400,
                )

            if not school_id:
                return JsonResponse(
                    {
                        "detail": "Missing required header: X-School-Id.",
                        "code": "missing_tenant",
                    },
                    status=400,
                )

            # Validate the school actually exists in this database
            school = School.objects.filter(pk=school_id).only("id", "name").first()
            if school is None:
                return JsonResponse(
                    {
                        "detail": "Unknown X-School-Id.",
                        "code": "invalid_tenant",
                    },
                    status=404,
                )

            # Attach for downstream view usage
            request.school_id = str(school_id)
            request.school = school
            set_current_school(school)

            return self.get_response(request)

        finally:
            # Always clear thread-local tenant context, even on exceptions
            clear_current_school()
