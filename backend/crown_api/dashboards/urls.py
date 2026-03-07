"""Canonical dashboard API URLs."""
from django.urls import path
from crown_api.dashboards.views import (
    DashboardAlertsView,
    DashboardDrilldownView,
    DashboardMeView,
    DashboardSummaryView,
)
from crown_api.dashboards.admissions import AdmissionsFunnelView
from crown_api.dashboards.finance import FinanceSummaryView
from crown_api.dashboards.academics import EnrollmentSnapshotView

urlpatterns = [
    # Legacy contract endpoints
    path("dashboards/me/", DashboardMeView.as_view(), name="dashboards-me"),
    path("dashboards/summary/", DashboardSummaryView.as_view(), name="dashboards-summary"),
    path("dashboards/drilldown/", DashboardDrilldownView.as_view(), name="dashboards-drilldown"),
    path("dashboards/alerts/", DashboardAlertsView.as_view(), name="dashboards-alerts"),

    # Tenant isolation dashboard endpoints
    path("dashboards/admissions/funnel/", AdmissionsFunnelView.as_view(), name="dashboards-admissions-funnel"),
    path("dashboards/finance/summary/", FinanceSummaryView.as_view(), name="dashboards-finance-summary"),
    path("dashboards/academics/enrollment/", EnrollmentSnapshotView.as_view(), name="dashboards-academics-enrollment"),

    # Existing canonical day-2 endpoint
    path("dashboard/me/", DashboardMeView.as_view(), name="dashboard-me"),
]
