from django.urls import path
from .views import FinancialAidSummaryView, FinancialAidDrilldownView
from .api import aid_applications, aid_awards, disburse_to_billing_run, financial_aid_metrics

urlpatterns = [
    path("summary/", FinancialAidSummaryView.as_view(), name="financial-aid-summary"),
    path("drilldown/", FinancialAidDrilldownView.as_view(), name="financial-aid-drilldown"),
    # Metrics Ã¢â‚¬â€ live DB-backed, school-scoped (replaces stub formerly in metrics_views.py)
    path("metrics/", financial_aid_metrics, name="financial-aid-metrics"),
    # Phase 4B: ledger-integrated aid endpoints
    path("applications/", aid_applications, name="financial-aid-applications"),
    path("awards/", aid_awards, name="financial-aid-awards"),
    path("billing-runs/<str:billing_run_id>/disburse/", disburse_to_billing_run, name="financial-aid-disburse-to-billing-run"),
]
