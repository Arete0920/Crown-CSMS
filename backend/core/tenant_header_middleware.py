from __future__ import annotations

import os
from dataclasses import replace
import re

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import APIException

from core.models import School
from core.tenant_models import clear_current_school, set_current_school
from crown_api.audit import audit_tenant_decision
from crown_api.tenant import (
    bind_tenant_context,
    build_tenant_context,
    clear_tenant_school_binding,
)


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


def _is_public_inquiry_post(request, path: str) -> bool:
    # Only capture and capability-based continuation resolve their school from
    # a public payload. Reads and staff updates retain normal tenant enforcement.
    return request.method == "POST" and re.fullmatch(
        r"/api/(?:v1/)?crm/inquiries(?:/[0-9a-fA-F-]{36}/start)?", path,
    ) is not None


def _is_platform_operator_path(path: str) -> bool:
    """Exact privileged schoolless paths, not public or school-scoped APIs."""
    uuid_pattern = (
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )
    return (
        path in {"/api/platform/schools", "/api/platform/schools/list"}
        or bool(re.fullmatch(rf"/api/platform/provisioning/{uuid_pattern}", path))
        or bool(re.fullmatch(rf"/api/v1/subscriptions/ops/{uuid_pattern}", path))
    )


def _record_tenant_decision(request, *, outcome: str, reason: str, required: bool = False) -> bool:
    """Persist tenant decisions; authorized overrides fail closed when evidence cannot persist."""
    try:
        audit_tenant_decision(request, outcome=outcome, reason=reason)
        return True
    except Exception:
        if required:
            return False
        return True


class TenantHeaderRequiredMiddleware:
    """
    Enforce and bind the canonical tenant context for protected API requests.

    This remains after authentication middleware so authenticated-school fallback
    and staff override authorization are available before business logic executes.
    Existing exemptions are intentionally unchanged during this migration lane.
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
        "/api/redoc",
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
            try:
                enforce_tenant_context(request)
            except TenantContextError as exc:
                return JsonResponse(exc.detail, status=exc.status_code)
            return self.get_response(request)
        finally:
            clear_current_school()


class TenantContextError(APIException):
    """Preserve tenant middleware denial payloads when DRF authenticates later."""

    def __init__(self, detail, *, status):
        self.status_code = status
        super().__init__(detail=detail)

def _tenant_context_error(request, detail, *, status):
    context = getattr(request, "crown_tenant", None)
    if context is not None:
        bind_tenant_context(request, replace(context, school=None))
    clear_tenant_school_binding(request)
    clear_current_school()
    return TenantContextError(detail, status=status)


def enforce_tenant_context(request) -> None:
    """Apply the same tenant contract before views and after late bearer auth.

    Authentication policy belongs to the existing middleware/authenticator chain.
    This guard neither authenticates requests nor relaxes its early denials.
    """
    if request.method == "OPTIONS":
        return

    if not getattr(settings, "TENANT_HEADER_REQUIRED", True):
        return

    path = getattr(request, "path", "") or ""
    normalized_path = path.rstrip("/") or "/"

    if not normalized_path.startswith("/api/"):
        return

    # Global operations cannot borrow a caller-selected tenant. Separate view
    # permissions require active platform-superuser identity.
    if _is_platform_operator_path(normalized_path):
        if "HTTP_X_SCHOOL_ID" in request.META or "HTTP_X_CROWN_SCHOOL_ID" in request.META:
            raise _tenant_context_error(
                request,
                {"detail": "School selector forbidden on global operations.",
                 "code": "platform_tenant_selector_forbidden"},
                status=400,
            )
        return

    # School-less DEV demo-reset credential probes must reach the ops guard.
    # The view rejects them before migrations or seeding. A school selector
    # always retains normal tenant header enforcement.
    if (
        request.method == "POST"
        and normalized_path == "/api/v1/system/demo-reset"
        and "X-School-Id" not in request.headers
        and "school_id" not in request.GET
    ):
        return

    if _is_public_inquiry_post(request, normalized_path) or any(
        normalized_path.startswith(prefix)
        for prefix in TenantHeaderRequiredMiddleware.EXEMPT_PREFIXES
    ):
        context = build_tenant_context(request)
        bind_tenant_context(request, context)
        if context.source == "header_invalid":
            _record_tenant_decision(
                request,
                outcome="denied",
                reason="invalid_tenant_header_exempt_route",
            )
            raise _tenant_context_error(
                request,
                {
                    "detail": "Invalid X-School-Id (must be UUID).",
                    "code": "invalid_tenant_header",
                },
                status=400,
            )
        return

    if _dev_open_dashboard_bypass_enabled() and _is_dashboard_api_path(normalized_path):
        return

    if _is_dashboard_api_path(normalized_path) and _is_production_runtime():
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise _tenant_context_error(
                request,
                {"detail": "Authentication credentials were not provided."},
                status=401,
            )

    context = build_tenant_context(request)
    bind_tenant_context(request, context)

    if context.source == "header_invalid":
        _record_tenant_decision(request, outcome="denied", reason="invalid_tenant_header")
        raise _tenant_context_error(
            request,
            {
                "detail": "Invalid X-School-Id (must be UUID).",
                "code": "invalid_tenant_header",
            },
            status=400,
        )

    if not context.school_id:
        _record_tenant_decision(request, outcome="denied", reason="missing_tenant")
        raise _tenant_context_error(
            request,
            {
                "detail": "Missing required header: X-School-Id.",
                "code": "missing_tenant",
            },
            status=400,
        )

    if context.override_requested and not context.override_authorized:
        _record_tenant_decision(request, outcome="denied", reason="override_not_authorized")
        raise _tenant_context_error(
            request,
            {"detail": "Not found.", "code": "tenant_access_denied"},
            status=404,
        )

    school = (
        School.objects.filter(pk=context.school_id, is_active=True)
        .only("id", "name", "is_active")
        .first()
    )
    if school is None:
        _record_tenant_decision(request, outcome="denied", reason="tenant_inactive_or_unknown")
        raise _tenant_context_error(
            request,
            {
                "detail": "Unknown X-School-Id.",
                "code": "invalid_tenant",
            },
            status=404,
        )

    if context.override_authorized and not _record_tenant_decision(
        request,
        outcome="authorized",
        reason="explicit_cross_school_override",
        required=True,
    ):
        raise _tenant_context_error(
            request,
            {
                "detail": "Tenant authorization evidence could not be persisted.",
                "code": "tenant_audit_unavailable",
            },
            status=503,
        )

    bind_tenant_context(request, replace(context, school=school))
    set_current_school(school)
