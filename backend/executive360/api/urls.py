from django.urls import path

from .views import ExecutiveSelfOverview

urlpatterns = [
    path("me/overview/", ExecutiveSelfOverview.as_view(), name="executive_360_self"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
