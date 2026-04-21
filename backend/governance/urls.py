from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.governance_dashboard, name="governance-dashboard"),
    path("services-status/", views.m365_services_status, name="m365-services-status"),
]
