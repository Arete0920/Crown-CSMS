from django.urls import path

from .views import campaign_collection, campaign_detail, campaign_touchpoint

urlpatterns = [
    path("campaigns/", campaign_collection, name="crm-marketing-campaigns"),
    path("campaigns/<uuid:campaign_id>/", campaign_detail, name="crm-marketing-campaign-detail"),
    path("campaigns/<uuid:campaign_id>/touchpoints/", campaign_touchpoint, name="crm-marketing-campaign-touchpoint"),
]
