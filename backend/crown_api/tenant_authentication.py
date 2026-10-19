"""Revalidate tenant authority after an existing DRF authenticator succeeds."""

from dataclasses import replace

from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication

from core.tenant_header_middleware import enforce_tenant_context
from core.tenant_models import clear_current_school
from crown_api.tenant import (
    bind_tenant_context,
    build_tenant_context,
    clear_tenant_school_binding,
)


def reconcile_authenticated_tenant(request, authenticated):
    """Replace pre-authentication scope using an already validated principal.

    DRF has not yet assigned request.user while an authenticator is running.
    Work on its underlying Django request so tenant resolution and audit cannot
    recursively trigger authentication. Preserve all existing tenant exemptions;
    even an exempt request receives fresh canonical metadata for its own guards.
    """
    raw_request = getattr(request, "_request", request)
    raw_request.user, raw_request.auth = authenticated
    clear_current_school()
    clear_tenant_school_binding(raw_request)
    if request is not raw_request:
        clear_tenant_school_binding(request)

    try:
        bind_tenant_context(raw_request, build_tenant_context(raw_request))
        enforce_tenant_context(raw_request)
    except Exception:
        context = getattr(raw_request, "crown_tenant", None)
        if context is not None:
            context = replace(context, school=None)
            bind_tenant_context(raw_request, context)
            if request is not raw_request:
                bind_tenant_context(request, context)
        clear_tenant_school_binding(raw_request)
        if request is not raw_request:
            clear_tenant_school_binding(request)
        clear_current_school()
        raise

    if request is not raw_request:
        bind_tenant_context(request, raw_request.crown_tenant)
    return authenticated


class TenantJWTAuthentication(SimpleJWTAuthentication):
    """Keep SimpleJWT validation while enforcing its authenticated tenant scope."""

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is None:
            return None
        return reconcile_authenticated_tenant(request, authenticated)
