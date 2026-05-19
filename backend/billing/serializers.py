from rest_framework import serializers

from .models import BillingRun, Invoice, InvoiceLine, InstallmentPlan, InstallmentScheduleItem


class BillingRunSerializer(serializers.ModelSerializer):
    """Read serializer for BillingRun."""

    class Meta:
        model = BillingRun
        fields = [
            "id",
            "school_id",
            "term",
            "run_type",
            "description",
            "amount_per_student",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InvoiceLineSerializer(serializers.ModelSerializer):
    """Read serializer for InvoiceLine."""

    class Meta:
        model = InvoiceLine
        fields = [
            "id",
            "school_id",
            "invoice_id",
            "student_id",
            "description",
            "amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    """Read serializer for Invoice, with nested lines."""

    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "school_id",
            "billing_run_id",
            "household_id",
            "total_amount",
            "due_on",
            "ledger_charge_id",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InstallmentPlanSerializer(serializers.ModelSerializer):
    """Read serializer for InstallmentPlan."""

    class Meta:
        model = InstallmentPlan
        fields = [
            "id",
            "school_id",
            "term",
            "name",
            "installment_count",
            "first_due_on",
            "cadence_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InstallmentScheduleItemSerializer(serializers.ModelSerializer):
    """Read serializer for InstallmentScheduleItem."""

    class Meta:
        model = InstallmentScheduleItem
        fields = [
            "id",
            "school_id",
            "plan_id",
            "household_id",
            "sequence",
            "due_on",
            "amount",
            "invoice_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
