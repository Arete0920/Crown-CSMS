"""
finance/serializers.py — DRF serializers for Finance & Tuition module.
"""
from __future__ import annotations

from rest_framework import serializers

from finance.models import (
    ChartAccount,
    FinanceAllocation,
    FinanceDonation,
    FinanceInvoice,
    FinanceInvoiceLine,
    FinanceObligation,
    FinancePayment,
    FinanceRefund,
    JournalBatch,
)


class ChartAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartAccount
        fields = ["id", "school", "code", "name", "account_type", "is_active"]
        read_only_fields = ["id"]


class ObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceObligation
        fields = [
            "id",
            "school",
            "payer_user",
            "obligation_type",
            "status",
            "description",
            "due_date",
            "amount_cents",
            "currency",
            "academic_year_label",
            "reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "created_at", "updated_at"]


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceInvoiceLine
        fields = ["id", "obligation", "amount_cents", "description"]
        read_only_fields = ["id"]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, required=False)

    class Meta:
        model = FinanceInvoice
        fields = [
            "id",
            "school",
            "payer_user",
            "status",
            "period_start",
            "period_end",
            "issued_at",
            "due_date",
            "subtotal_cents",
            "total_cents",
            "currency",
            "note",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "issued_at", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancePayment
        fields = [
            "id",
            "school",
            "payer_user",
            "status",
            "amount_cents",
            "currency",
            "processor",
            "processor_payment_id",
            "idempotency_key",
            "received_at",
            "settled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "created_at", "updated_at"]


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceAllocation
        fields = ["id", "school", "payment", "obligation", "amount_cents", "created_at"]
        read_only_fields = ["id", "school", "created_at"]


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceRefund
        fields = [
            "id",
            "school",
            "payment",
            "status",
            "amount_cents",
            "currency",
            "processor",
            "processor_refund_id",
            "idempotency_key",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "created_at", "updated_at"]


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceDonation
        fields = [
            "id",
            "school",
            "donor_user",
            "status",
            "amount_cents",
            "currency",
            "fund_code",
            "memo",
            "is_recurring",
            "recurring_rule",
            "next_run_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "created_at", "updated_at"]
