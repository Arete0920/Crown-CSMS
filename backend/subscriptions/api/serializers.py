"""
Subscriptions API serializers.
"""
from rest_framework import serializers

from subscriptions.models import Feature, Plan, PlanEntitlement, TenantSubscription


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "key", "name", "description"]


class PlanEntitlementSerializer(serializers.ModelSerializer):
    feature_key = serializers.CharField(source="feature.key", read_only=True)
    feature_name = serializers.CharField(source="feature.name", read_only=True)

    class Meta:
        model = PlanEntitlement
        fields = ["feature_key", "feature_name", "enabled", "limit_int"]


class PlanSerializer(serializers.ModelSerializer):
    entitlements = PlanEntitlementSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "sort_order",
            "pricing_currency",
            "base_monthly",
            "per_student_monthly",
            "entitlements",
        ]


class PlanListSerializer(serializers.ModelSerializer):
    """Lightweight plan serializer (no entitlements) for list endpoints."""

    class Meta:
        model = Plan
        fields = ["id", "code", "name", "is_active", "sort_order", "base_monthly"]


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanListSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TenantSubscription
        fields = [
            "id",
            "school_id",
            "plan",
            "plan_id",
            "started_at",
            "ended_at",
            "is_trial",
        ]
        read_only_fields = ["id", "school_id", "started_at", "ended_at"]
