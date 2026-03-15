from django.urls import path

from .academics import EnrollmentSnapshotView
from .admissions import AdmissionsFunnelDashboard
from .finance import FinanceSummaryDashboard
from .views import DashboardSummaryView


urlpatterns = [
    path("admissions/funnel/", AdmissionsFunnelDashboard.as_view(), name="dashboard-admissions-funnel"),
    path("finance/summary/", FinanceSummaryDashboard.as_view(), name="dashboard-finance-summary"),
    path("academics/enrollment/", EnrollmentSnapshotView.as_view(), name="dashboard-academics-enrollment"),
    path('<slug:dashboard_key>/summary', DashboardSummaryView.as_view(), name='dashboard-summary'),
]
