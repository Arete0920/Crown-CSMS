from django.urls import path
from . import views

urlpatterns = [
    path("",                              views.create_session,    name="ep-wizard-create"),
    path("<uuid:session_id>/configure/",  views.configure_session, name="ep-wizard-configure"),
    path("<uuid:session_id>/capacities/", views.set_capacities,    name="ep-wizard-capacities"),
    path("<uuid:session_id>/commit/",     views.commit_session,    name="ep-wizard-commit"),
    path("<uuid:session_id>/verify/",     views.verify_session,    name="ep-wizard-verify"),
]
