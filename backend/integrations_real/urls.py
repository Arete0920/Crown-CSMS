from django.urls import path

from .api import connectors_health, connectors_status

urlpatterns = [
    path("health/", connectors_health, name="integrations-real-health"),
    path("status/", connectors_status, name="integrations-real-status"),
]
