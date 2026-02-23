from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import DonorViewSet, CampaignViewSet, advancement_metrics

router = DefaultRouter()
router.register(r"donors", DonorViewSet, basename="advancement-donors")
router.register(r"campaigns", CampaignViewSet, basename="advancement-campaigns")

urlpatterns = [
    path("metrics/", advancement_metrics, name="advancement-metrics"),
    path("", include(router.urls)),
]
