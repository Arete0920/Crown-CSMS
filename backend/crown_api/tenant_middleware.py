# backend/crown_api/tenant_middleware.py
from __future__ import annotations

from django.http import JsonResponse
from django.urls import resolve

from .tenant import TENANT_ATTR, resolve_tenant_school_id

# These endpoints must not require a tenant.
PUBLIC_PATH_PREFIXES = (
    "/health/",
    "/api/auth/login/",
    "/api/auth/refresh/",
    "/api/auth/me/",  # auth itself; tenant can be derived from JWT
)

PUBLIC_URL_NAMES = set([
    # If you later prefer names instead of paths, add them here.
])


class TenantContextMiddleware:
    """
    Stamps request.tenant_school_id early so views can enforce tenant consistently.

    IMPORTANT:
    - We do NOT block here by default (blocking belongs in the view layer / decorators),
      because some endpoints are intentionally public.
    - For protected endpoints, you MUST call require_tenant() / get_tenant_school_id(required=True)
      in the view.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        res = resolve_tenant_school_id(request)
        setattr(request, TENANT_ATTR, res.school_id)
        # Store resolution metadata so validation layer knows what happened
        setattr(request, "_tenant_resolution_source", res.source)
        setattr(request, "_tenant_header_present", res.header_present)

        # Set _crown_school_override_id for audit trail when staff overrides via header
        if res.header_present and res.school_id and res.source == "header":
            # Check both request.user (middleware) and request._force_auth_user (DRF tests)
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                user = getattr(request, "_force_auth_user", None)
            
            if user and getattr(user, "is_authenticated", False):
                user_school = getattr(user, "school_id", None)
                # Only set override ID if user is staff and actually overriding
                if (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)) and user_school:
                    if str(user_school) != str(res.school_id):
                        setattr(request, "_crown_school_override_id", res.school_id)

        return self.get_response(request)
