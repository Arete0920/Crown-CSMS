"""Runtime boundary for demo/CI-only ops endpoints.

The ops summary/alerts surface is intentionally unauthenticated for bounded demo
and CI proof. Keep the public routes unavailable unless the runtime is explicitly
a development environment or the current Azure host is clearly the DEV app.
"""

from __future__ import annotations

import os
from functools import wraps

from django.conf import settings
from django.http import Http404


_DEV_ENVIRONMENTS = {"dev", "development", "local", "test", "testing"}
_PROD_ENVIRONMENTS = {"prod", "production", "live"}


def _configured_environment() -> str:
    """Return the first explicit application environment marker."""
    values = (
        getattr(settings, "ENVIRONMENT", ""),
        getattr(settings, "CROWN_ENV", ""),
        getattr(settings, "DJANGO_ENV", ""),
        os.getenv("ENVIRONMENT", ""),
        os.getenv("CROWN_ENV", ""),
        os.getenv("DJANGO_ENV", ""),
    )
    for value in values:
        normalized = str(value or "").strip().lower()
        if normalized:
            return normalized
    return ""


def demo_ops_runtime_allowed() -> bool:
    """Allow only DEV/test runtimes; reject conflicting settings and live hosts."""
    values = (
        getattr(settings, "ENVIRONMENT", ""),
        getattr(settings, "CROWN_ENV", ""),
        getattr(settings, "DJANGO_ENV", ""),
        os.getenv("ENVIRONMENT", ""),
        os.getenv("CROWN_ENV", ""),
        os.getenv("DJANGO_ENV", ""),
    )
    configured = [str(value).strip().lower() for value in values if str(value or "").strip()]
    if any(value in _PROD_ENVIRONMENTS for value in configured):
        return False
    if any(value not in _DEV_ENVIRONMENTS for value in configured):
        return False

    hostname = str(os.getenv("WEBSITE_HOSTNAME", "") or "").strip().lower()
    if hostname:
        app_name = hostname.split(".", 1)[0]
        if not (app_name == "crown-api-dev" or app_name.endswith("-dev")):
            return False

    # Unlabelled local runtimes fail closed; the recognized DEV Azure host is
    # sufficient even where older deployments omitted an explicit marker.
    return bool(configured or hostname)


def demo_ops_only(view):
    """Wrap a view so the route exists only in an authorized demo/DEV runtime."""
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not demo_ops_runtime_allowed():
            raise Http404
        return view(request, *args, **kwargs)

    return guarded
