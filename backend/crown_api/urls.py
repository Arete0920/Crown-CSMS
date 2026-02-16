"""
URL configuration for crown_api project.
"""
from django.urls import include, path
from django.views.generic import RedirectView
from crown_api.health_views import health, health_version, system_health
from crown_api.version_views import version
from crown_api.views import director_dashboard_page, director_router
from crown_api.ops_views import ops_summary, ops_alerts
from crown_api.rbac_views import finance_guardrail_proof
from crown_api.audit_views import recent_audit_events
from crown_api.auth_views import login, refresh, me
from crown_api.system_views import whoami
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("", RedirectView.as_view(url="director/", permanent=False)),
    path("health/", health, name="health"),
    path("api/health/", health, name="api_health"),
    path("api/system/health/", system_health, name="system_health"),
    path("health/version/", health_version, name="health_version"),
    
    # Gate 1C: WhoAmI proof endpoint (requires auth)
    path("api/system/whoami/", whoami, name="system_whoami"),
    
    # Version endpoint (public, no auth required)
    path("api/v1/version/", version, name="version"),
    
    # Ops summary (public read-only, for demo proof)
    path("api/ops/summary/", ops_summary, name="ops_summary"),
    
    # Ops alerts (public read-only, for demo proof)
    path("api/ops/alerts/", ops_alerts, name="ops_alerts"),
    
    # RBAC proof endpoint
    path("api/system/rbac/finance-proof/", finance_guardrail_proof, name="finance_guardrail_proof"),
    
    # Audit log endpoint
    path("api/system/audit/recent/", recent_audit_events, name="recent_audit_events"),
    
    # JWT Auth endpoints
    path("api/auth/login/", login, name="auth_login"),
    path("api/auth/refresh/", refresh, name="auth_refresh"),
    path("api/auth/me/", me, name="auth_me"),
    
    # Authentication URLs (must come BEFORE api/ includes)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Canonical API
    path("api/v1/", include("crown_api.api_v1_urls")),
    
    # Back-compat alias: /api/* behaves like /api/v1/*
    path("api/", include("crown_api.api_v1_urls")),
    
    # Curriculum (read-only, demo-safe)
    path("api/curriculum/", include("curriculum.urls")),
    
    # Integrations (webhooks, etc.)
    path("api/integrations/", include("integrations.urls")),
    
    # Authentication URLs (login, logout, password reset, etc.)
    path("accounts/", include("django.contrib.auth.urls")),
    
    # Director routing - persona-specific URLs all use same view
    path("director/", director_router, name="director_router"),
    path("director/aid/", director_dashboard_page, {'persona': 'aid'}, name="director_aid"),
    path("director/admissions/", director_dashboard_page, {'persona': 'admissions'}, name="director_admissions"),
    path("director/finance/", director_dashboard_page, {'persona': 'finance'}, name="director_finance"),
    path("director/registrar/", director_dashboard_page, {'persona': 'registrar'}, name="director_registrar"),
]

# Admin URLs added after app initialization
try:
    from django.contrib.admin import site
    urlpatterns.append(path("admin/", site.urls))
except Exception:
    pass
