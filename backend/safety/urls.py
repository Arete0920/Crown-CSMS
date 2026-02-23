from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import IncidentViewSet, safety_metrics

router = DefaultRouter()
router.register(r"incidents", IncidentViewSet, basename="safety-incidents")

urlpatterns = [
    path("metrics/", safety_metrics, name="safety-metrics"),
    path("", include(router.urls)),
]
