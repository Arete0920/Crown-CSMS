"""Canonical dashboard API URLs."""
from django.urls import path
from crown_api.dashboards.views import (
    AdminDashboardView,
    DashboardAlertsView,
    DashboardDrilldownView,
    DashboardMeView,
    DashboardMs365QuickPanelView,
    DashboardSummaryView,
    TeacherDashboardView,
    ParentDashboardView,
    StudentDashboardView,
    FinanceDashboardView,
    AdmissionsDashboardView,
    BoardDashboardView,
    RegistrarDashboardView,
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
    path("dashboards/ms365/quick-panel/", DashboardMs365QuickPanelView.as_view(), name="dashboards-ms365-quick-panel"),

    # Tenant isolation dashboard endpoints
    path("dashboards/admissions/funnel/", AdmissionsFunnelView.as_view(), name="dashboards-admissions-funnel"),
    path("dashboards/finance/summary/", FinanceSummaryView.as_view(), name="dashboards-finance-summary"),
    path("dashboards/academics/enrollment/", EnrollmentSnapshotView.as_view(), name="dashboards-academics-enrollment"),

    # Existing canonical day-2 endpoints
    path("dashboard/me/", DashboardMeView.as_view(), name="dashboard-me"),
    path("dash/admin/", AdminDashboardView.as_view()),
    path("dash/teacher/", TeacherDashboardView.as_view()),
    path("dash/parent/", ParentDashboardView.as_view()),
    path("dash/student/", StudentDashboardView.as_view()),
    path("dash/finance/", FinanceDashboardView.as_view()),
    path("dash/admissions/", AdmissionsDashboardView.as_view()),
    path("dash/board/", BoardDashboardView.as_view()),
    path("dash/registrar/", RegistrarDashboardView.as_view()),
]
