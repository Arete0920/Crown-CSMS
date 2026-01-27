"""
Canonical API v1 routes.
All /api/v1/* and /api/* routes resolve through here.
"""
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Authentication
    path("auth/token/", TokenObtainPairView.as_view(), name="v1_token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="v1_token_refresh"),
    
    # Keep the same effective ordering you already rely on.
    # If any patterns collide, earlier includes win.
    path("", include("households.urls")),
    path("", include("crown_api.billing_api.urls")),
    path("", include("crown_api.exports.urls")),
    path("", include("crown_api.api_urls")),
]
