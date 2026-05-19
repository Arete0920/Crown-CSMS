from rest_framework import serializers
from .models import LedgerAccount, Charge, Payment, Allocation


class LedgerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerAccount
        fields = ["id", "school_id", "household", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = [
            "id", "school_id", "account", "description",
            "amount", "is_void", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "school_id", "account", "source", "reference",
            "amount", "is_void", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = [
            "id", "school_id", "payment", "charge",
            "amount", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

