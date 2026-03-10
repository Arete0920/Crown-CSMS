from django.urls import path

from .views import DashboardSummaryView


urlpatterns = [
    path('<slug:dashboard_key>/summary', DashboardSummaryView.as_view(), name='dashboard-summary'),
]
