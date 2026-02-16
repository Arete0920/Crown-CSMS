# backend/crown_api/tenant_decorators.py
from __future__ import annotations

from functools import wraps
from django.http import JsonResponse

from .tenant import get_tenant_school_id


def require_tenant(view_func):
    """
    Enforces tenant resolution for non-public endpoints.
    Returns 403 if tenant cannot be resolved.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            _ = get_tenant_school_id(request, required=True)
        except PermissionError:
            return JsonResponse({"detail": "tenant_required"}, status=403)
        return view_func(request, *args, **kwargs)

    return _wrapped
