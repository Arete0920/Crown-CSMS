from django.urls import path

from .views import (
    InvoicesCSVExportView,
    InstallmentScheduleCSVExportView,
)

urlpatterns = [
    path("exports/invoices.csv", InvoicesCSVExportView.as_view(), name="exports-invoices-csv"),
    path(
        "exports/installment-schedule.csv",
        InstallmentScheduleCSVExportView.as_view(),
        name="exports-installment-schedule-csv",
    ),
]
