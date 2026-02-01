"""
Canonical API v1 routes.
All /api/v1/* and /api/* routes resolve through here.
"""
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from applications.views_admissions import admissions_summary, admissions_drilldown

urlpatterns = [
    # Authentication
    path("auth/token/", TokenObtainPairView.as_view(), name="v1_token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="v1_token_refresh"),

    # Dashboards (Day 2 read-only endpoints)
    path("", include("crown_api.dashboards.urls")),
    
    # Admissions funnel (frozen contract)
    path("admissions/summary/", admissions_summary, name="admissions_summary"),
    path("admissions/drilldown/", admissions_drilldown, name="admissions_drilldown"),
    
    # Keep the same effective ordering you already rely on.
    # If any patterns collide, earlier includes win.
    path("", include("households.urls")),
    path("", include("crown_api.billing_api.urls")),
    path("", include("crown_api.exports.urls")),
    path("", include("crown_api.api_urls")),
    # Financial Aid endpoints
    path("financial-aid/", include("financial_aid.urls")),
]
