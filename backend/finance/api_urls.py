"""
finance/api_urls.py — Finance & Tuition module URL patterns.
Mounted at: /api/finance/ (see crown_api/urls.py)
"""
from django.urls import path
from finance import api_views as views

urlpatterns = [
    # Admin: obligations
    path("obligations/", views.obligations, name="finance-obligations"),

    # Admin: invoices
    path("invoices/", views.invoice_list, name="finance-invoice-list"),
    path("invoices/create-from-obligations/", views.invoice_create_from_obligations, name="finance-invoice-create"),

    # Parent: balance
    path("parent/balance/", views.parent_balance, name="finance-parent-balance"),

    # Payments
    path("payments/intent/", views.payment_intent_create, name="finance-payment-intent"),
    path("payments/<int:payment_id>/settle/", views.payment_settle, name="finance-payment-settle"),
    path("payments/<int:payment_id>/refund/", views.refund_create, name="finance-refund-create"),

    # Donations
    path("donations/", views.donation_list, name="finance-donation-list"),
    path("donations/create/", views.donation_create, name="finance-donation-create"),
]
