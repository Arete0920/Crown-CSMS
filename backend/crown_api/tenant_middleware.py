from __future__ import annotations

from .tenant import CANONICAL_TENANT_ATTR, bind_tenant_context, build_tenant_context


class TenantContextMiddleware:
    """Bind tenant metadata only when the enforcing middleware has not already done so."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        context = getattr(request, CANONICAL_TENANT_ATTR, None)
        if context is None:
            context = build_tenant_context(request)
            bind_tenant_context(request, context)

        return self.get_response(request)
