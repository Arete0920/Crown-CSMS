# backend/facops/api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from facops.api.views import (
    AlertViewSet,
    AssetViewSet,
    DrillViewSet,
    LocationViewSet,
    SafetyIncidentViewSet,
    VisitorLogViewSet,
    WorkOrderViewSet,
    facilities_summary,
    security_summary,
)

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"facilities/locations", LocationViewSet, basename="facilities-locations")
router.register(r"facilities/assets", AssetViewSet, basename="facilities-assets")
router.register(r"facilities/work-orders", WorkOrderViewSet, basename="facilities-work-orders")
router.register(r"security/incidents", SafetyIncidentViewSet, basename="security-incidents")
router.register(r"security/drills", DrillViewSet, basename="security-drills")
router.register(r"security/visitor-logs", VisitorLogViewSet, basename="security-visitor-logs")
router.register(r"security/alerts", AlertViewSet, basename="security-alerts")

urlpatterns = [
    path("facilities/summary/", facilities_summary, name="facilities-summary"),
    path("security/summary/", security_summary, name="security-summary"),
    path("", include(router.urls)),
]
