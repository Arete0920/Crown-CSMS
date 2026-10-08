"""
URL configuration for crown_api project.
"""

import logging
import os
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from crown_api.wizard_registry import get_wizard_urlpatterns  # single source of truth
from crown_api.api.wizards import wizard_discovery
from crown_api.health_views import health, health_version, system_health
from crown_api.views_integrity import integrity
from crown_api.version_views import version
from crown_api.views import director_dashboard_page, director_router
from crown_api.ops_views import ops_summary as _ops_summary, ops_alerts as _ops_alerts
from crown_api.ops_route_guard import demo_ops_only
from crown_api.rbac_views import finance_guardrail_proof
from crown_api.audit_views import recent_audit_events
from crown_api.auth_views import login, refresh, me
from crown_api.dev_token_views import dev_token
from crown_api.system_views import whoami
from solomon.guidance_views import guidance_view


logger = logging.getLogger(__name__)


def _production_like_runtime() -> bool:
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


def _guard_api_docs(view):
    """Hide schema/docs in production unless explicitly enabled for staff."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not _production_like_runtime():
            return view(request, *args, **kwargs)

        if not bool(getattr(settings, "CROWN_API_DOCS_ENABLED", False)):
            raise Http404

        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise Http404
        if not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
            raise Http404

        return view(request, *args, **kwargs)

    return wrapped


# Public demo/CI proof endpoints are wrapped at the routing boundary so an
# unknown or production-like runtime cannot expose their operational metadata.
ops_summary = demo_ops_only(_ops_summary)
ops_alerts = demo_ops_only(_ops_alerts)

urlpatterns = [
    # Separate grantor tenancy: explicit SGO membership, no school-tenant API shortcut.
    path("sgo/api/v1/", include("jireh_sgo.urls")),
    path("api/solomon/guidance/", guidance_view, name="solomon-guidance"),
    path("", RedirectView.as_view(url="director/", permanent=False)),
    path("api/v1/graduation/", include("graduation.urls")),
    path(
        "api/v1/wizards/", wizard_discovery, name="wizard-discovery"
    ),  # discovery: single source of truth
    *get_wizard_urlpatterns(),  # wizard SDK: single source of truth in wizard_registry.py
    path("health/", health, name="health"),
    path("api/health/", health, name="api_health"),
    path("api/integrity/", integrity, name="api_integrity"),
    path("api/schema/", _guard_api_docs(SpectacularAPIView.as_view()), name="schema"),
    path(
        "api/docs/",
        _guard_api_docs(SpectacularSwaggerView.as_view(url_name="schema")),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        _guard_api_docs(SpectacularRedocView.as_view(url_name="schema")),
        name="redoc",
    ),
    path("api/system/health/", system_health, name="system_health"),
    path("health/version/", health_version, name="health_version"),
    # Gate 1C: WhoAmI proof endpoint (requires auth)
    path("api/system/whoami/", whoami, name="system_whoami"),
    # Version endpoint (public, no auth required)
    path("api/v1/version/", version, name="version"),
    # Ops summary (public only in explicit DEV/demo runtime)
    path("api/ops/summary/", ops_summary, name="ops_summary"),
    # Ops alerts (public only in explicit DEV/demo runtime)
    path("api/ops/alerts/", ops_alerts, name="ops_alerts"),
    # RBAC proof endpoint
    path(
        "api/system/rbac/finance-proof/",
        finance_guardrail_proof,
        name="finance_guardrail_proof",
    ),
    # Audit log endpoint
    path("api/system/audit/recent/", recent_audit_events, name="recent_audit_events"),
    # JWT Auth endpoints
    path("api/auth/login/", login, name="auth_login"),
    path("api/auth/refresh/", refresh, name="auth_refresh"),
    path("api/auth/me/", me, name="auth_me"),
    # Demo-only dev token endpoint (fail-closed)
    path("api/dev/token/", dev_token, name="dev_token"),
    # Legacy daycare compatibility routes map the former Little Lambs URL to canonical Aftercare/Diadem behavior; keep them before the api_v1 catch-all.
    path("api/v1/little-lambs/", include("aftercare.urls")),
    path("api/little-lambs/", include("aftercare.urls")),
    # Canonical API. Specific dashboard routes must precede each broad alias.
    path("api/v1/dashboards/", include("crown_api.dashboards.urls")),
    path("api/v1/", include("crown_api.api_v1_urls")),
    # Back-compat alias: /api/dashboards/* mirrors /api/v1/dashboards/*.
    path("api/dashboards/", include("crown_api.dashboards.urls")),
    # Back-compat alias: /api/* behaves like /api/v1/*.
    path("api/", include("crown_api.api_v1_urls")),
    # Curriculum (read-only, demo-safe)
    path("api/curriculum/", include("curriculum.urls")),
    # Classroom (read-only, demo-safe)
    path("api/classroom/", include("classroom.urls")),
    # Student 360 overview (per-student dashboard data)
    path("api/student360/", include("student360.api.urls")),
    # Executive 360 overview (school-wide metrics for admins)
    path("api/executive360/", include("executive360.api.urls")),
    # Finance & Tuition Management (Phase 8)
    path("api/finance/", include("finance.api_urls")),
    # Institutional accounting / ERP-Lite business office
    path("api/accounting/", include("apps.accounting.urls")),
    # Platform Operations (super-admin, cross-tenant, no X-School-ID required)
    path("api/platform/", include("platform_ops.urls")),
    # Subscriptions & Entitlements
    path("api/v1/subscriptions/", include("subscriptions.api.urls")),
    # Crown Admin Module Tier Management
    path("api/v1/admin/modules/", include("subscriptions.urls")),
    # Integrations (webhooks, etc.)
    path("api/integrations/", include("integrations.urls")),
    # Microsoft SSO (session-based auth)
    path("auth/", include("msauth.urls")),
    # AAD-backed identity endpoints (Bearer token, Entra ID)
    # Uses /api/iam/ prefix to avoid collision with legacy /api/auth/me/
    path("api/iam/", include("core.auth.urls")),
    # Authentication URLs (login, logout, password reset, etc.)
    path("accounts/", include("django.contrib.auth.urls")),
    # Director routing - persona-specific URLs all use same view
    path("director/", director_router, name="director_router"),
    path(
        "director/aid/",
        director_dashboard_page,
        {"persona": "aid"},
        name="director_aid",
    ),
    path(
        "director/admissions/",
        director_dashboard_page,
        {"persona": "admissions"},
        name="director_admissions",
    ),
    path(
        "director/finance/",
        director_dashboard_page,
        {"persona": "finance"},
        name="director_finance",
    ),
    path(
        "director/registrar/",
        director_dashboard_page,
        {"persona": "registrar"},
        name="director_registrar",
    ),
]

# Admin URLs added after app initialization
try:
    from django.contrib.admin import site

    urlpatterns.append(path("admin/", site.urls))
except Exception:
    logger.exception("crown_api.urls: failed to register admin URL")

