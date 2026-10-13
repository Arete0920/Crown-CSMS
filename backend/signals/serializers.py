from rest_framework import serializers
from .models import (
    SignalDefinition,
    StudentRiskSnapshot,
    SignalEvent,
    InterventionCase,
    InterventionAction,
    BoardExecutiveMetric,
)


class SignalDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignalDefinition
        fields = ["id", "key", "name", "description", "severity_weight", "is_active", "rule"]


class StudentRiskSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRiskSnapshot
        fields = ["student_id", "as_of_date", "risk_score", "risk_level", "drivers"]


class SignalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignalEvent
        fields = ["student_id", "signal_key", "weight", "summary", "details", "fired_at"]


class InterventionCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterventionCase
        fields = [
            "id", "student_id", "opened_at", "closed_at",
            "status", "priority", "reason", "linked_signals",
            "owner_user_id", "owner_account_id", "review_at", "version", "last_action_at",
        ]


class InterventionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterventionAction
        fields = ["id", "case_id", "action_type", "note", "created_by_user_id", "created_by_account_id", "created_at"]


class BoardExecutiveMetricSerializer(serializers.ModelSerializer):
    enrollment_health = serializers.IntegerField(read_only=True, allow_null=True)
    financial_health = serializers.IntegerField(read_only=True, allow_null=True)
    culture_health = serializers.IntegerField(read_only=True, allow_null=True)
    mission_health = serializers.IntegerField(read_only=True, allow_null=True)
    calculation_status = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # The current engine stores placeholders for these unwired indexes.
        # They are not assessed health scores, including when stored as zero.
        for field in ("enrollment_health", "financial_health", "culture_health", "mission_health"):
            data[field] = None
        data["calculation_status"] = "awaiting_validated_metric_definitions"
        return data

    class Meta:
        model = BoardExecutiveMetric
        fields = [
            "as_of_date",
            "enrollment_health", "financial_health", "culture_health",
            "mission_health", "retention_risk",
            "highlights", "watchlist",
            "calculation_status",
        ]
