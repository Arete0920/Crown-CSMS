from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import EmployeeViewSet, hr_metrics

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"employees", EmployeeViewSet, basename="hr-employees")

urlpatterns = [
    path("metrics/", hr_metrics, name="hr-metrics"),
    path("", include(router.urls)),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
