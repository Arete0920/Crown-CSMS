from rest_framework import serializers

from .models import PredictiveModelRun


class PredictiveModelRunSerializer(serializers.ModelSerializer):
    """Read serializer for PredictiveModelRun audit records."""

    school_id = serializers.UUIDField(source="school.id", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = PredictiveModelRun
        fields = [
            "id",
            "model_name",
            "run_date",
            "school_id",
            "school_name",
            "input_snapshot_date",
            "output_json",
            "confidence_interval_low",
            "confidence_interval_high",
            "feature_importance",
        ]
        read_only_fields = fields
