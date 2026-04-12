from django.urls import path
from discipline.api.views import (
    DisciplineIncidentsListCreate,
    DisciplineIncidentDetail,
    DisciplineIncidentActions,
    DisciplineMetrics,
)

urlpatterns = [
    path("incidents/", DisciplineIncidentsListCreate.as_view(), name="discipline_incidents"),
    path("incidents/<uuid:incident_id>/", DisciplineIncidentDetail.as_view(), name="discipline_incident_detail"),
    path("incidents/<uuid:incident_id>/actions/", DisciplineIncidentActions.as_view(), name="discipline_incident_actions"),
    path("metrics/", DisciplineMetrics.as_view(), name="discipline_metrics"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
