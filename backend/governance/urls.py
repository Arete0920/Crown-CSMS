from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.governance_dashboard, name="governance-dashboard"),
]
