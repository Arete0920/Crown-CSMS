# backend/core/tenant_header_middleware.py
from __future__ import annotations

import os

from django.conf import settings
from django.http import JsonResponse

from core.models import School
from core.tenant_models import set_current_school, clear_current_school
from crown_api.tenant import resolve_tenant_school_id


def _is_production_runtime() -> bool:
    env = (
        str(getattr(settings, "CROWN_ENV", "") or "")
        or str(getattr(settings, "DJANGO_ENV", "") or "")
        or str(getattr(settings, "ENVIRONMENT", "") or "")
        or str(os.getenv("CROWN_ENV", "") or "")
        or str(os.getenv("DJANGO_ENV", "") or "")
        or str(os.getenv("ENVIRONMENT", "") or "")
        or str(os.getenv("AZURE_ENVIRONMENT", "") or "")
    ).strip().lower()
    return env in {"prod", "production", "live"} or bool(os.getenv("WEBSITE_HOSTNAME"))


def _dev_open_dashboard_bypass_enabled() -> bool:
    return bool(getattr(settings, "CROWN_DEV_OPEN_API", False)) and not _is_production_runtime()


def _is_dashboard_api_path(path: str) -> bool:
    return path.startswith(("/api/dashboards", "/api/v1/dashboards"))


class TenantHeaderRequiredMiddleware:
    """
    Enforces tenant resolution for /api/* calls.

    Policy (in priority order):
    1. Unauthenticated production dashboard calls return 401 before tenant validation
    2. X-School-Id header is used when present (primary)
    3. Authenticated user.school_id is the fallback for users without a header
    4. Missing tenant returns 400

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
        "/api/dev/token",
        "/api/payments/webhooks/",
        "/api/v1/payments/webhooks/",
        "/api/schema",
        "/api/docs",
        "/api/director/force_seed_user",
        "/api/v1/admissions/submit",
        "/api/admissions/submit",
        "/api/v1/admissions/public-config",
        "/api/admissions/public-config",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.method == "OPTIONS":
                return self.get_response(request)

            if not getattr(settings, "TENANT_HEADER_REQUIRED", True):
                return self.get_response(request)

            path = getattr(request, "path", "") or ""
            normalized_path = path.rstrip("/") or "/"

            if not normalized_path.startswith("/api/"):
                return self.get_response(request)

            for prefix in self.EXEMPT_PREFIXES:
                if normalized_path.startswith(prefix):
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

            if _dev_open_dashboard_bypass_enabled() and _is_dashboard_api_path(normalized_path):
                return self.get_response(request)

            if _is_dashboard_api_path(normalized_path) and _is_production_runtime():
                user = getattr(request, "user", None)
                if not user or not getattr(user, "is_authenticated", False):
                    return JsonResponse(
                        {"detail": "Authentication credentials were not provided."},
                        status=401,
                    )

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

            school = School.objects.filter(pk=school_id).only("id", "name").first()
            if school is None:
                return JsonResponse(
                    {
                        "detail": "Unknown X-School-Id.",
                        "code": "invalid_tenant",
                    },
                    status=404,
                )

            request.school_id = str(school_id)
            request.school = school
            set_current_school(school)

            return self.get_response(request)

        finally:
            clear_current_school()
