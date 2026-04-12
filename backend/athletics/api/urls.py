# backend/athletics/api/urls.py
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from athletics.api.views import (
    AthleteClearanceViewSet,
    AthleteEligibilityViewSet,
    EventViewSet,
    FacilityViewSet,
    SeasonViewSet,
    SportViewSet,
    TeamCoachViewSet,
    TeamRosterViewSet,
    TeamViewSet,
)

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"sports", SportViewSet, basename="ath_sports")
router.register(r"seasons", SeasonViewSet, basename="ath_seasons")
router.register(r"teams", TeamViewSet, basename="ath_teams")
router.register(r"facilities", FacilityViewSet, basename="ath_facilities")
router.register(r"rosters", TeamRosterViewSet, basename="ath_rosters")
router.register(r"coaches", TeamCoachViewSet, basename="ath_coaches")
router.register(r"events", EventViewSet, basename="ath_events")
router.register(r"clearance", AthleteClearanceViewSet, basename="ath_clearance")
router.register(r"eligibility", AthleteEligibilityViewSet, basename="ath_eligibility")

urlpatterns = [path("", include(router.urls))]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
