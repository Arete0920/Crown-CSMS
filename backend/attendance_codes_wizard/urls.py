from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="attendance_codes_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="attendance_codes_wizard_configure"),
    path("<uuid:session_id>/stage_codes/", views.stage_codes, name="attendance_codes_wizard_stage_codes"),
    path("<uuid:session_id>/commit/", views.commit_session, name="attendance_codes_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="attendance_codes_wizard_verify"),
]
