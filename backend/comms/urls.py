"""
comms/urls.py Ã¢â‚¬â€ URL patterns for the communications API.

Mounted at /api/comms/ in crown_api/urls.py.
Routes are delegated to comms/api/urls.py which owns the full view set.
"""
from django.urls import include, path

urlpatterns = [
    path("", include("comms.api.urls")),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
