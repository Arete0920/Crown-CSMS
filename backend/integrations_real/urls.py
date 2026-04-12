from django.urls import path

from .api import connectors_health, connectors_status

urlpatterns = [
    path("health/", connectors_health, name="integrations-real-health"),
    path("status/", connectors_status, name="integrations-real-status"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
