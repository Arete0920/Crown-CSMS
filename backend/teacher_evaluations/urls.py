from django.urls import path

from . import api

urlpatterns = [
    path("cycles/", api.cycles, name="teacher-evaluation-cycles"),
    path("cycles/<uuid:cycle_id>/", api.cycle_detail, name="teacher-evaluation-cycle-detail"),
    path("cycles/<uuid:cycle_id>/observations/", api.observations, name="teacher-evaluation-observations"),
    path("observations/<uuid:observation_id>/submit/", api.submit_observation, name="teacher-observation-submit"),
    path("observations/<uuid:observation_id>/responses/", api.observation_response, name="teacher-observation-response"),
]
