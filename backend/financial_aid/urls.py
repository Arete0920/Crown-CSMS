from django.urls import path
from .views import FinancialAidSummaryView, FinancialAidDrilldownView
from .api import aid_applications, aid_awards, disburse_to_billing_run

urlpatterns = [
    path("summary/", FinancialAidSummaryView.as_view(), name="financial-aid-summary"),
    path("drilldown/", FinancialAidDrilldownView.as_view(), name="financial-aid-drilldown"),
    # Phase 4B: ledger-integrated aid endpoints
    path("applications/", aid_applications, name="financial-aid-applications"),
    path("awards/", aid_awards, name="financial-aid-awards"),
    path("billing-runs/<str:billing_run_id>/disburse/", disburse_to_billing_run, name="financial-aid-disburse-to-billing-run"),
]
