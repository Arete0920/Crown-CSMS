from django.urls import path

from .views import (
    InvoicesCSVExportView,
    InstallmentScheduleCSVExportView,
    HouseholdsCSVExportView,
    StudentsCSVExportView,
    StaffCSVExportView,
)

urlpatterns = [
    path("exports/invoices.csv", InvoicesCSVExportView.as_view(), name="exports-invoices-csv"),
    path(
        "exports/installment-schedule.csv",
        InstallmentScheduleCSVExportView.as_view(),
        name="exports-installment-schedule-csv",
    ),

    # 0091
    path("exports/households.csv", HouseholdsCSVExportView.as_view(), name="exports-households-csv"),
    path("exports/students.csv", StudentsCSVExportView.as_view(), name="exports-students-csv"),
    path("exports/staff.csv", StaffCSVExportView.as_view(), name="exports-staff-csv"),
]
