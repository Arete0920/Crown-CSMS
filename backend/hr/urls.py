from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import EmployeeViewSet, hr_metrics

router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="hr-employees")

urlpatterns = [
    path("metrics/", hr_metrics, name="hr-metrics"),
    path("", include(router.urls)),
]
