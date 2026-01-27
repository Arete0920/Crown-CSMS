"""
Canonical API v1 routes.
All /api/v1/* and /api/* routes resolve through here.
"""
from django.urls import include, path

urlpatterns = [
    # Keep the same effective ordering you already rely on.
    # If any patterns collide, earlier includes win.
    path("", include("households.urls")),
    path("", include("crown_api.billing_api.urls")),
    path("", include("crown_api.exports.urls")),
    path("", include("crown_api.api_urls")),
]
