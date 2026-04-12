from django.urls import path

from . import views

urlpatterns = [
    path("",                              views.create_session,   name="grade_scale_create"),
    path("<uuid:session_id>/configure/",  views.configure_session, name="grade_scale_configure"),
    path("<uuid:session_id>/bands/",      views.set_bands,         name="grade_scale_bands"),
    path("<uuid:session_id>/weights/",    views.set_weights,       name="grade_scale_weights"),
    path("<uuid:session_id>/commit/",     views.commit_session,    name="grade_scale_commit"),
    path("<uuid:session_id>/verify/",     views.verify_session,    name="grade_scale_verify"),
]
