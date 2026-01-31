from django.urls import path
from .views import FinancialAidSummaryView, FinancialAidDrilldownView

urlpatterns = [
    path("summary/", FinancialAidSummaryView.as_view(), name="financial-aid-summary"),
    path("drilldown/", FinancialAidDrilldownView.as_view(), name="financial-aid-drilldown"),
]
