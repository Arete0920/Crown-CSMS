from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import EmployeeViewSet, hr_metrics
from .requirement_api import staff_requirements

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"employees", EmployeeViewSet, basename="hr-employees")

urlpatterns = [
    path("staff-requirements/", staff_requirements, name="hr-staff-requirements"),
    path("metrics/", hr_metrics, name="hr-metrics"),
    path("", include(router.urls)),
]
