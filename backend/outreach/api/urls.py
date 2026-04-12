from django.urls import include, path
from rest_framework.routers import DefaultRouter

from outreach.api.views import (
    BadgeAwardViewSet,
    BadgeViewSet,
    OpportunityViewSet,
    PartnerOrganizationViewSet,
    ReflectionPromptViewSet,
    ServiceGoalViewSet,
    ServiceLogViewSet,
)

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"partners", PartnerOrganizationViewSet, basename="outreach-partners")
router.register(r"opportunities", OpportunityViewSet, basename="outreach-opportunities")
router.register(r"service-logs", ServiceLogViewSet, basename="outreach-service-logs")
router.register(r"goals", ServiceGoalViewSet, basename="outreach-goals")
router.register(r"prompts", ReflectionPromptViewSet, basename="outreach-prompts")
router.register(r"badges", BadgeViewSet, basename="outreach-badges")
router.register(r"badge-awards", BadgeAwardViewSet, basename="outreach-badge-awards")

urlpatterns = [
    path("", include(router.urls)),
]
