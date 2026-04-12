# backend/transportation/api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from transportation.api.views import (
    AssignmentViewSet,
    DispatchViewSet,
    DriverViewSet,
    RideEventViewSet,
    RouteViewSet,
    StopViewSet,
    StudentRiderViewSet,
    VehicleViewSet,
)

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"vehicles", VehicleViewSet, basename="vehicles")
router.register(r"drivers", DriverViewSet, basename="drivers")
router.register(r"routes", RouteViewSet, basename="routes")
router.register(r"stops", StopViewSet, basename="stops")
router.register(r"riders", StudentRiderViewSet, basename="riders")
router.register(r"assignments", AssignmentViewSet, basename="assignments")
router.register(r"events", RideEventViewSet, basename="events")
router.register(r"dispatch", DispatchViewSet, basename="dispatch")

urlpatterns = [path("", include(router.urls))]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
