from django.urls import path

from . import views

urlpatterns = [
    path("", views.create_session),
    path("<uuid:session_id>/configure/", views.configure_session),
    path("<uuid:session_id>/codes/", views.define_codes),
    path("<uuid:session_id>/commit/", views.commit_session),
    path("<uuid:session_id>/verify/", views.verify_session),
]
