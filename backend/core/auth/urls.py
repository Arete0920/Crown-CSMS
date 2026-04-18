"""
core/auth/urls.py - URL patterns for AAD-backed identity endpoints.

Mounted at /api/iam/ in crown_api/urls.py to avoid collision with the
legacy Crown JWT routes already registered at /api/auth/.
"""
from django.urls import path

from .views import health_auth, me

urlpatterns = [
    path("me/",          me,          name="iam_me"),
    path("health-auth/", health_auth, name="iam_health_auth"),
]
