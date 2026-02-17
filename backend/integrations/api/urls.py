from django.urls import path
from integrations.api.views import TeamsPreview

urlpatterns = [
    path("teams/preview/", TeamsPreview.as_view(), name="teams_preview"),
]
