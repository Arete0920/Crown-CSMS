"""
Subscriptions API URL configuration.

Mounted at /api/v1/subscriptions/ in crown_api/urls.py.

  GET  subscriptions/me/entitlements/    — entitlement snapshot for current tenant
  GET  subscriptions/plans/              — list all active plans
  GET  subscriptions/features/           — list all feature keys
  GET  subscriptions/ops/<school_id>/    — ops: get school subscription [IsAdminUser]
  POST subscriptions/ops/<school_id>/    — ops: set school plan [IsAdminUser]
"""
from django.urls import path

from subscriptions.api import views

urlpatterns = [
    path("me/entitlements/", views.me_entitlements, name="subscriptions_me_entitlements"),
    path("plans/", views.plan_list, name="subscriptions_plan_list"),
    path("features/", views.feature_list, name="subscriptions_feature_list"),
    path(
        "ops/<uuid:school_id>/",
        views.ops_school_subscription,
        name="subscriptions_ops_school",
    ),
]
