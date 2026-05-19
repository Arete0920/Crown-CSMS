from rest_framework import serializers
from .models import (
    PaymentIntentRecord,
    GatewayEvent,
    ProviderDispute,
    StatementExportRequest,
    PaymentSupportException,
    BankStatementImport,
    BankStatementEntry,
    PayoutBankMatch,
)


class PaymentIntentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntentRecord
        fields = [
            "id", "school_id", "provider", "invoice_id", "household_id",
            "amount", "currency", "client_reference_id",
            "provider_intent_id", "provider_payment_id", "status",
            "metadata", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GatewayEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = GatewayEvent
        fields = [
            "id", "school_id", "provider", "event_id", "event_type",
            "provider_intent_id", "provider_payment_id", "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProviderDisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderDispute
        fields = [
            "id", "school_id", "provider", "dispute_id",
            "provider_payment_id", "amount", "currency",
            "status", "reason", "opened_at", "closed_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StatementExportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementExportRequest
        fields = [
            "id", "school_id", "household_id", "format", "status",
            "file_name", "filters", "created_at", "generated_at",
        ]
        read_only_fields = ["id", "created_at", "generated_at"]


class PaymentSupportExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSupportException
        fields = [
            "id", "school_id", "provider", "category",
            "severity", "status", "message",
            "retry_count", "resolved_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BankStatementEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementEntry
        fields = [
            "id", "school_id", "statement_import", "posted_date",
            "description", "reference", "amount", "currency",
            "is_matched", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BankStatementImportSerializer(serializers.ModelSerializer):
    entries = BankStatementEntrySerializer(many=True, read_only=True)

    class Meta:
        model = BankStatementImport
        fields = [
            "id", "school_id", "status", "source_name",
            "row_count", "created_at", "processed_at",
            "entries",
        ]
        read_only_fields = ["id", "created_at", "processed_at"]


class PayoutBankMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutBankMatch
        fields = [
            "id", "school_id", "payout_batch", "bank_entry",
            "status", "amount_delta", "date_delta_days", "note",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

