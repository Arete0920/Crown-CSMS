from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="billing_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="billing_wizard_configure"),
    path("<uuid:session_id>/plans/", views.save_plans, name="billing_wizard_plans"),
    path("<uuid:session_id>/fees/", views.save_fees, name="billing_wizard_fees"),
    path("<uuid:session_id>/commit/", views.commit_session, name="billing_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="billing_wizard_verify"),
]
