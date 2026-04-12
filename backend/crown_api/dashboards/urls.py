from django.urls import path

from .academics import EnrollmentSnapshotView
from .admissions import AdmissionsFunnelDashboard
from .finance import FinanceSummaryDashboard
from .views import DashboardSummaryView
from .views import dashboard_me, dashboard_summary, dashboard_drilldown, dashboard_alerts


urlpatterns = [
    # Role contract API endpoints (test_dashboards_role_contract)
    path("me/", dashboard_me, name="dashboard-me"),
    path("summary/", dashboard_summary, name="dashboard-summary-api"),
    path("drilldown/", dashboard_drilldown, name="dashboard-drilldown"),
    path("alerts/", dashboard_alerts, name="dashboard-alerts"),
    # Legacy / v1 dashboard views
    path("admissions/funnel/", AdmissionsFunnelDashboard.as_view(), name="dashboard-admissions-funnel"),
    path("finance/summary/", FinanceSummaryDashboard.as_view(), name="dashboard-finance-summary"),
    path("academics/enrollment/", EnrollmentSnapshotView.as_view(), name="dashboard-academics-enrollment"),
    path('<slug:dashboard_key>/summary', DashboardSummaryView.as_view(), name='dashboard-summary'),
]
