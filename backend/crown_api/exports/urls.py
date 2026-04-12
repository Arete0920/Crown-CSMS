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
    StatementsCSVExportView,
    StatementLinesCSVExportView,
    YearEndTuitionPaidCSVExportView,
    PaymentsQuickBooksCSVExportView,
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

    # 0093
    path("exports/statements.csv", StatementsCSVExportView.as_view(), name="exports-statements-csv"),

    # 0094
    path(
        "exports/statement-lines.csv",
        StatementLinesCSVExportView.as_view(),
        name="exports-statement-lines-csv",
    ),

    # 0095-A
    path(
        "exports/year-end/tuition-paid.csv",
        YearEndTuitionPaidCSVExportView.as_view(),
        name="exports-year-end-tuition-paid-csv",
    ),

    # 0096-A
    path(
        "exports/accounting/payments-qb.csv",
        PaymentsQuickBooksCSVExportView.as_view(),
        name="exports-accounting-payments-qb-csv",
    ),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
