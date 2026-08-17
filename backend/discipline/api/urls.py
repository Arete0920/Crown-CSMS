from django.urls import path
from discipline.api.views import (
    DisciplineIncidentsListCreate,
    DisciplineIncidentDetail,
    DisciplineIncidentActions,
)
from discipline.api.secure_views import RestrictedDisciplineMetrics

urlpatterns = [
    path("incidents/", DisciplineIncidentsListCreate.as_view(), name="discipline_incidents"),
    path("incidents/<uuid:incident_id>/", DisciplineIncidentDetail.as_view(), name="discipline_incident_detail"),
    path("incidents/<uuid:incident_id>/actions/", DisciplineIncidentActions.as_view(), name="discipline_incident_actions"),
    path("metrics/", RestrictedDisciplineMetrics.as_view(), name="discipline_metrics"),
]