from django.urls import path

from apps.accounting import api

app_name = "accounting"

urlpatterns = [
    path("vendors/", api.vendors, name="vendors"),
    path("funds/", api.funds, name="funds"),
    path("dimensions/", api.dimensions, name="dimensions"),
    path("purchase-orders/", api.purchase_orders, name="purchase-orders"),
    path(
        "purchase-orders/<uuid:po_id>/submit/",
        api.purchase_order_action,
        {"action": "submit"},
        name="purchase-order-submit",
    ),
    path(
        "purchase-orders/<uuid:po_id>/approve/",
        api.purchase_order_action,
        {"action": "approve"},
        name="purchase-order-approve",
    ),
    path("bills/", api.payable_bills, name="bills"),
    path(
        "bills/<uuid:bill_id>/approve/",
        api.payable_bill_action,
        {"action": "approve"},
        name="bill-approve",
    ),
    path(
        "bills/<uuid:bill_id>/post/",
        api.payable_bill_action,
        {"action": "post"},
        name="bill-post",
    ),
    path(
        "bills/<uuid:bill_id>/void/",
        api.payable_bill_action,
        {"action": "void"},
        name="bill-void",
    ),
    path("budgets/", api.budgets, name="budgets"),
    path("budgets/<uuid:budget_id>/approve/", api.budget_approve, name="budget-approve"),
    path("reports/trial-balance/", api.trial_balance_report, name="trial-balance"),
    path("reports/income-statement/", api.income_statement_report, name="income-statement"),
    path("reports/balance-sheet/", api.balance_sheet_report, name="balance-sheet"),
    path(
        "reports/budgets/<uuid:budget_id>/variance/",
        api.budget_variance_report,
        name="budget-variance",
    ),
]
