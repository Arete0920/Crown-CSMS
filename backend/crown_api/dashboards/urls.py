"""
Dashboard API URLs - Read-only endpoints
"""
from django.urls import path
from crown_api.dashboards.admissions import AdmissionsFunnelView
from crown_api.dashboards.finance import FinanceSummaryView
from crown_api.dashboards.academics import EnrollmentSnapshotView

urlpatterns = [
    path("dashboards/admissions/funnel/", AdmissionsFunnelView.as_view(), name="dashboard_admissions_funnel"),
    path("dashboards/finance/summary/", FinanceSummaryView.as_view(), name="dashboard_finance_summary"),
    path("dashboards/academics/enrollment/", EnrollmentSnapshotView.as_view(), name="dashboard_academics_enrollment"),
]
