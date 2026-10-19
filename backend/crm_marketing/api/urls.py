from django.urls import path

from .views import campaign_collection, campaign_detail, campaign_touchpoint
from .inquiries import inquiry_collection, inquiry_start, inquiry_update

urlpatterns = [
    path("inquiries/", inquiry_collection, name="crm-inquiries"),
    path("inquiries/<uuid:inquiry_id>/start/", inquiry_start, name="crm-inquiry-start"),
    path("inquiries/<uuid:inquiry_id>/", inquiry_update, name="crm-inquiry-update"),
    path("campaigns/", campaign_collection, name="crm-marketing-campaigns"),
    path("campaigns/<uuid:campaign_id>/", campaign_detail, name="crm-marketing-campaign-detail"),
    path("campaigns/<uuid:campaign_id>/touchpoints/", campaign_touchpoint, name="crm-marketing-campaign-touchpoint"),
]
