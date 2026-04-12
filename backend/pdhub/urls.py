from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import PDResourceViewSet, PDSessionViewSet, pd_metrics

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"resources", PDResourceViewSet, basename="pd-resources")
router.register(r"sessions", PDSessionViewSet, basename="pd-sessions")

urlpatterns = [
    path("metrics/", pd_metrics, name="pd-metrics"),
    path("", include(router.urls)),
]
