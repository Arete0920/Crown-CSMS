"""Pilot-only SGO routes: organization authorization on every request."""
from django.urls import path

from . import api

urlpatterns = [
    path("organizations/<uuid:organization_id>/summary/", api.summary, name="sgo-summary"),
    path("organizations/<uuid:organization_id>/programs/", api.programs, name="sgo-programs"),
    path("organizations/<uuid:organization_id>/applications/", api.applications, name="sgo-applications"),
    path("organizations/<uuid:organization_id>/applications/<uuid:application_id>/review/", api.review, name="sgo-review"),
    path("organizations/<uuid:organization_id>/awards/", api.awards, name="sgo-awards"),
]
