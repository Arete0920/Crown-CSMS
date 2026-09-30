from django.urls import path
from .views import survey_collection, survey_detail, survey_response_submit, survey_insights_view

urlpatterns = [
    path("surveys/", survey_collection, name="survey-collection"),
    path("surveys/<uuid:survey_id>/", survey_detail, name="survey-detail"),
    path("surveys/<uuid:survey_id>/responses/", survey_response_submit, name="survey-response-submit"),
    path("insights/", survey_insights_view, name="survey-insights"),
]
