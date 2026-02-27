"""
Dashboard API URLs - Read-only endpoints
"""
from django.urls import path
from crown_api.dashboards.admissions import AdmissionsFunnelView
from crown_api.dashboards.finance import FinanceSummaryView
from crown_api.dashboards.academics import EnrollmentSnapshotView
from crown_api.dashboards.views import (
    DashboardMeView,
    DashboardSummaryView,
    DashboardDrilldownView,
    DashboardAlertsView,
)

urlpatterns = [
    # Legacy per-module endpoints (existing contracts — do not rename)
    path("dashboards/admissions/funnel/", AdmissionsFunnelView.as_view(), name="dashboard_admissions_funnel"),
    path("dashboards/finance/summary/", FinanceSummaryView.as_view(), name="dashboard_finance_summary"),
    path("dashboards/academics/enrollment/", EnrollmentSnapshotView.as_view(), name="dashboard_academics_enrollment"),

    # Crown unified dashboard API (Phase 10 — role-based)
    path("dashboards/me/", DashboardMeView.as_view(), name="dashboard_me"),
    path("dashboards/summary/", DashboardSummaryView.as_view(), name="dashboard_summary"),
    path("dashboards/drilldown/", DashboardDrilldownView.as_view(), name="dashboard_drilldown"),
    path("dashboards/alerts/", DashboardAlertsView.as_view(), name="dashboard_alerts"),
]
