from django.urls import path
from section_scheduler_wizard import views

urlpatterns = [
    path("", views.create_session),
    path("<uuid:session_id>/configure/", views.configure),
    path("<uuid:session_id>/sections/", views.set_sections),
    path("<uuid:session_id>/commit/", views.commit),
    path("<uuid:session_id>/verify/", views.verify),
]

