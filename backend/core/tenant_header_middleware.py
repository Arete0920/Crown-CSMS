from __future__ import annotations

import os

from django.conf import settings
from django.http import JsonResponse

from core.models import School
from core.tenant_models import clear_current_school, set_current_school
from crown_api.tenant import bind_tenant_context, build_tenant_context


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
    Enforce and bind the canonical tenant context for protected API requests.

    This remains after authentication middleware so authenticated-school fallback
    and staff override authorization are available before business logic executes.
    Existing exemptions are intentionally unchanged during the first migration lane.
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
                    context = build_tenant_context(request)
                    if context.source == "header_invalid":
                        return JsonResponse(
                            {
                                "detail": "Invalid X-School-Id (must be UUID).",
                                "code": "invalid_tenant_header",
                            },
                            status=400,
                        )
                    bind_tenant_context(request, context)
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

            context = build_tenant_context(request)

            if context.source == "header_invalid":
                return JsonResponse(
                    {
                        "detail": "Invalid X-School-Id (must be UUID).",
                        "code": "invalid_tenant_header",
                    },
                    status=400,
                )

            if not context.school_id:
                return JsonResponse(
                    {
                        "detail": "Missing required header: X-School-Id.",
                        "code": "missing_tenant",
                    },
                    status=400,
                )

            if context.override_requested and not context.override_authorized:
                return JsonResponse(
                    {"detail": "Not found.", "code": "tenant_access_denied"},
                    status=404,
                )

            school = (
                School.objects.filter(pk=context.school_id, is_active=True)
                .only("id", "name", "is_active")
                .first()
            )
            if school is None:
                return JsonResponse(
                    {
                        "detail": "Unknown X-School-Id.",
                        "code": "invalid_tenant",
                    },
                    status=404,
                )

            context = build_tenant_context(request, school=school)
            bind_tenant_context(request, context)
            set_current_school(school)
            return self.get_response(request)

        finally:
            clear_current_school()
