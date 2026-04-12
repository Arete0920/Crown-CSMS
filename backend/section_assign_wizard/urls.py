from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="section_assign_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="section_assign_wizard_configure"),
    path("<uuid:session_id>/load/", views.load_students, name="section_assign_wizard_load"),
    path("<uuid:session_id>/stage/", views.stage_roster, name="section_assign_wizard_stage"),
    path("<uuid:session_id>/commit/", views.commit_session, name="section_assign_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="section_assign_wizard_verify"),
]
