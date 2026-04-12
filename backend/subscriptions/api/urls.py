"""
Subscriptions API URL configuration.

Mounted at /api/v1/subscriptions/ in crown_api/urls.py.

  GET  subscriptions/me/entitlements/    Ã¢â‚¬â€ entitlement snapshot for current tenant
  GET  subscriptions/plans/              Ã¢â‚¬â€ list all active plans
  GET  subscriptions/features/           Ã¢â‚¬â€ list all feature keys
  GET  subscriptions/ops/<school_id>/    Ã¢â‚¬â€ ops: get school subscription [IsAdminUser]
  POST subscriptions/ops/<school_id>/    Ã¢â‚¬â€ ops: set school plan [IsAdminUser]
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

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
