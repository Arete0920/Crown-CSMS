from django.urls import path
from integrations.api.views import TeamsPreview

urlpatterns = [
    path("teams/preview/", TeamsPreview.as_view(), name="teams_preview"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
