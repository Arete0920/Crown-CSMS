from django.urls import path

from .views import (
    ExecutiveChartDrilldownView,
    ExecutiveGhostContextView,
    ExecutiveKpiDrilldownView,
    ExecutiveSelfOverview,
)

urlpatterns = [
    path("me/overview/", ExecutiveSelfOverview.as_view(), name="executive_360_self"),
    path("me/kpi-drilldown/<str:kpi_key>/", ExecutiveKpiDrilldownView.as_view(), name="executive_360_kpi_drilldown"),
    path("me/chart-drilldown/<str:chart_key>/", ExecutiveChartDrilldownView.as_view(), name="executive_360_chart_drilldown"),
    path("me/ghost-context/", ExecutiveGhostContextView.as_view(), name="executive_360_ghost_context"),
]
