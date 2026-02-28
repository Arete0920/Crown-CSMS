"""
Tenant-aware middleware for the tenants app.

NOTE: Crown2026 already ships two tenant middleware layers:
  - core.tenant_header_middleware.TenantHeaderRequiredMiddleware (enforces X-School-Id header)
  - crown_api.tenant_middleware.TenantContextMiddleware (resolves + attaches school to request)

The classes below are additive layers:

  TenantMiddleware — attaches request.tenant_profile (TenantProfile ORM object) after the
      base school_id is resolved by TenantContextMiddleware.

  RequireTenantMiddleware — explicit block for any /api/ path that is NOT a platform op
      and has no resolved school.  Complements TenantHeaderRequiredMiddleware with a
      secondary safety net scoped to the tenants app.

Both are optional. TenantMiddleware is useful for views that need rich TenantProfile access
without a per-view ORM call.  RequireTenantMiddleware is a no-op when
TenantHeaderRequiredMiddleware is active (which it is by default in Crown2026 settings).
"""
from __future__ import annotations

import logging

from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)

# Paths that are exempt from tenant requirements (platform-level endpoints are cross-tenant)
_PLATFORM_PREFIXES = (
    "/api/platform/",
    "/api/health/",
    "/api/integrity/",
    "/api/system/",
    "/api/auth/",
    "/api/dev/",
    "/api/ops/",
    "/api/iam/",
    "/health/",
    "/api/v1/version/",
    "/accounts/",
    "/auth/",
    "/admin/",
    "/director/",
    "/api/v1/wizards/",
    "/api/v1/graduation/",
)


class TenantMiddleware:
    """
    Attaches request.tenant_profile (TenantProfile | None) after school_id is resolved.

    This runs *after* TenantContextMiddleware (which sets request.school_id).
    If no school_id is resolved, or the school has no TenantProfile, tenant_profile is None.

    Usage (place after TenantContextMiddleware in MIDDLEWARE):
        'tenants.middleware.TenantMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        self._attach_tenant_profile(request)
        return self.get_response(request)

    @staticmethod
    def _attach_tenant_profile(request: HttpRequest) -> None:
        request.tenant_profile = None
        school_id = getattr(request, "school_id", None)
        if not school_id:
            return
        try:
            from tenants.models import TenantProfile  # noqa: PLC0415
            request.tenant_profile = TenantProfile.objects.select_related("school").get(
                school_id=school_id
            )
        except TenantProfile.DoesNotExist:
            pass
        except Exception as exc:  # pragma: no cover
            logger.warning("TenantMiddleware: could not attach tenant_profile: %s", exc)


class RequireTenantMiddleware:
    """
    Secondary safety net: blocks /api/* requests that have no resolved school_id.

    Exempt paths (platform ops, health, auth, etc.) bypass this check.
    When TenantHeaderRequiredMiddleware is active this middleware is effectively a no-op,
    but it provides defence-in-depth if the primary middleware is ever removed.

    Usage (place after TenantContextMiddleware in MIDDLEWARE):
        'tenants.middleware.RequireTenantMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if self._should_block(request):
            return JsonResponse(
                {"error": "X-School-ID header is required for this endpoint.", "code": "TENANT_REQUIRED"},
                status=400,
            )
        return self.get_response(request)

    @staticmethod
    def _should_block(request: HttpRequest) -> bool:
        path = request.path_info
        # Only enforce on /api/ paths
        if not path.startswith("/api/"):
            return False
        # Exempt platform / infra prefixes
        if any(path.startswith(p) for p in _PLATFORM_PREFIXES):
            return False
        # Block if no school_id resolved on the request
        return not bool(getattr(request, "school_id", None))
