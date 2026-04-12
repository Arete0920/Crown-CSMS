from django.urls import path
from .views import ParentSelfOverview

urlpatterns = [
    path("me/overview/", ParentSelfOverview.as_view(), name="parent_360_self"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
