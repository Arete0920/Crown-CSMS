from django.urls import path
from section_scheduler_wizard import views
from crown_api.views_scheduling import my_schedule

urlpatterns = [
    path("my-schedule/", my_schedule),
    path("", views.create_session),
    path("<uuid:session_id>/configure/", views.configure),
    path("<uuid:session_id>/options/", views.options),
    path("<uuid:session_id>/sections/", views.set_sections),
    path("<uuid:session_id>/commit/", views.commit),
    path("<uuid:session_id>/verify/", views.verify),
    path("<uuid:session_id>/undo/", views.undo_publication),
]
