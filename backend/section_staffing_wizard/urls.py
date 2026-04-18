from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="section_staffing_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="section_staffing_wizard_configure"),
    path("<uuid:session_id>/load_sections/", views.load_sections, name="section_staffing_wizard_load_sections"),
    path("<uuid:session_id>/stage_assignments/", views.stage_assignments, name="section_staffing_wizard_stage_assignments"),
    path("<uuid:session_id>/commit/", views.commit_session, name="section_staffing_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="section_staffing_wizard_verify"),
]
