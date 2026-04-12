from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="guardian_household_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="guardian_household_wizard_configure"),
    path("<uuid:session_id>/add_guardians/", views.add_guardians, name="guardian_household_wizard_add_guardians"),
    path("<uuid:session_id>/link_students/", views.link_students, name="guardian_household_wizard_link_students"),
    path("<uuid:session_id>/commit/", views.commit_session, name="guardian_household_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="guardian_household_wizard_verify"),
]
