from django.urls import path

from .views import OpenInvoicesView, PaymentsApplyView, PaymentsCreateView, PaymentsRecordView
from .drf_views import BillingRunCreateApiView

urlpatterns = [
    path(
        "billing/households/<uuid:household_id>/open-invoices/",
        OpenInvoicesView.as_view(),
        name="billing-open-invoices",
    ),
    path("billing/payments/", PaymentsCreateView.as_view(), name="billing-payments-create"),
    path("billing/payments/record/", PaymentsRecordView.as_view(), name="billing-payments-record"),
    path(
        "billing/payments/<uuid:payment_id>/apply/",
        PaymentsApplyView.as_view(),
        name="billing-payments-apply",
    ),
    path("billing/runs/api/", BillingRunCreateApiView.as_view(), name="billing-runs-api-create"),
]
