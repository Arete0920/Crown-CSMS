from django.urls import path

from .views import (
    InvoicesCSVExportView,
    InstallmentScheduleCSVExportView,
    HouseholdsCSVExportView,
    StudentsCSVExportView,
    StaffCSVExportView,
    LedgerChargesCSVExportView,
    LedgerAllocationsCSVExportView,
    PaymentsCSVExportView,
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

    # 0092
    path("exports/ledger-charges.csv", LedgerChargesCSVExportView.as_view(), name="exports-ledger-charges-csv"),
    path(
        "exports/ledger-allocations.csv",
        LedgerAllocationsCSVExportView.as_view(),
        name="exports-ledger-allocations-csv",
    ),
    path("exports/payments.csv", PaymentsCSVExportView.as_view(), name="exports-payments-csv"),
]
