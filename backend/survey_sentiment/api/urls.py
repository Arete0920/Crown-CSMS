from django.urls import path

from .views import survey_drafts, survey_draft_detail

urlpatterns = [
    path("surveys/", survey_drafts, name="survey-intelligence-drafts"),
    path("surveys/<uuid:survey_id>/", survey_draft_detail, name="survey-intelligence-draft-detail"),
]
