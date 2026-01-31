"""
URL configuration for crown_api project.
"""
from django.urls import include, path
from django.views.generic import RedirectView
from crown_api.health_views import health, health_version
from crown_api.version_view import version
from crown_api.views import director_dashboard_page, director_router
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("", RedirectView.as_view(url="director/", permanent=False)),
    path("health/", health, name="health"),
    path("api/health/", health, name="api_health"),
    path("health/version/", health_version, name="health_version"),
    
    # Version endpoint (public, no auth required)
    path("api/v1/version/", version, name="version"),
    
    # Authentication URLs (must come BEFORE api/ includes)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Canonical API
    path("api/v1/", include("crown_api.api_v1_urls")),
    
    # Back-compat alias: /api/* behaves like /api/v1/*
    path("api/", include("crown_api.api_v1_urls")),
    
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
