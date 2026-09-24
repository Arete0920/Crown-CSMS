from django.urls import path

from .api import current_state, event_history, transition

urlpatterns = [
    path("students/<uuid:student_id>/", current_state, name="accountability-current-state"),
    path("students/<uuid:student_id>/events/", event_history, name="accountability-event-history"),
    path("transition/", transition, name="accountability-transition"),
]
