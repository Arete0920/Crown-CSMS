from django.urls import path
from . import scope_views, views

urlpatterns = [
    path("", views.create_session, name="scheduling_wizard_create"),
    path("scope-options/", scope_views.scope_options, name="scheduling_wizard_scope_options"),
    path("<uuid:session_id>/configure/", views.configure_session, name="scheduling_wizard_configure"),
    path("<uuid:session_id>/courses/", views.save_courses, name="scheduling_wizard_courses"),
    path("<uuid:session_id>/sections/", views.stage_sections, name="scheduling_wizard_sections"),
    path("<uuid:session_id>/commit/", views.commit_session, name="scheduling_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="scheduling_wizard_verify"),
]