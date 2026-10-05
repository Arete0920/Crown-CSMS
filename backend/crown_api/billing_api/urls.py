from django.urls import path
from rest_framework.permissions import IsAuthenticated

from core.permissions import CrownModulePermission

from .views import (
    HouseholdBillingPayersView,
    HouseholdBillingResponsibilityRulesView,
    MyPayerSharesView,
    OpenInvoicesView,
    PayerAllocationAttributionView,
    PaymentsApplyView,
    PaymentsCreateView,
    PaymentsRecordView,
)
from .drf_views import BillingRunCreateApiView


FINANCE_WRITE_PERMISSION_CLASSES = (
    IsAuthenticated,
    CrownModulePermission("finance.edit"),
)


urlpatterns = [
    path(
        "billing/households/<uuid:household_id>/payers/",
        HouseholdBillingPayersView.as_view(),
        name="billing-household-payers",
    ),
    path(
        "billing/households/<uuid:household_id>/responsibility-rules/",
        HouseholdBillingResponsibilityRulesView.as_view(),
        name="billing-household-responsibility-rules",
    ),
    path(
        "billing/my-payer-shares/",
        MyPayerSharesView.as_view(),
        name="billing-my-payer-shares",
    ),
    path(
        "billing/payer-attributions/",
        PayerAllocationAttributionView.as_view(),
        name="billing-payer-attributions",
    ),
    path(
        "billing/households/<uuid:household_id>/open-invoices/",
        OpenInvoicesView.as_view(),
        name="billing-open-invoices",
    ),
    path(
        "billing/payments/",
        PaymentsCreateView.as_view(permission_classes=FINANCE_WRITE_PERMISSION_CLASSES),
        name="billing-payments-create",
    ),
    path("billing/payments/record/", PaymentsRecordView.as_view(), name="billing-payments-record"),
    path(
        "billing/payments/<uuid:payment_id>/apply/",
        PaymentsApplyView.as_view(permission_classes=FINANCE_WRITE_PERMISSION_CLASSES),
        name="billing-payments-apply",
    ),
    path(
        "billing/runs/api/",
        BillingRunCreateApiView.as_view(permission_classes=FINANCE_WRITE_PERMISSION_CLASSES),
        name="billing-runs-api-create",
    ),
]
