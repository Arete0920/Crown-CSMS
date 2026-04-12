from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="grade_weights_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="grade_weights_wizard_configure"),
    path("<uuid:session_id>/stage_categories/", views.stage_categories, name="grade_weights_wizard_stage_categories"),
    path("<uuid:session_id>/commit/", views.commit_session, name="grade_weights_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="grade_weights_wizard_verify"),
]
