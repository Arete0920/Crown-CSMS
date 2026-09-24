from rest_framework import serializers

from .models import AccountabilityEvent, AccountabilityState


class AccountabilityStateSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(read_only=True)
    responsible_user_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = AccountabilityState
        fields = [
            "id",
            "school_id",
            "student_id",
            "normal_state",
            "emergency_state",
            "location_code",
            "responsible_user_id",
            "expected_destination",
            "source_domain",
            "source_record_id",
            "version",
            "updated_at",
        ]
        read_only_fields = [
            "id", "school_id", "student_id", "normal_state", "emergency_state",
            "location_code", "responsible_user_id", "expected_destination",
            "source_domain", "source_record_id", "version", "updated_at",
        ]


class AccountabilityEventSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(read_only=True)
    actor_user_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = AccountabilityEvent
        fields = [
            "id",
            "school_id",
            "student_id",
            "event_type",
            "from_normal_state",
            "to_normal_state",
            "from_emergency_state",
            "to_emergency_state",
            "location_code",
            "actor_user_id",
            "source_domain",
            "source_record_id",
            "context",
            "state_version",
            "occurred_at",
        ]
        read_only_fields = [
            "id", "school_id", "student_id", "event_type", "from_normal_state",
            "to_normal_state", "from_emergency_state", "to_emergency_state",
            "location_code", "actor_user_id", "source_domain", "source_record_id",
            "context", "state_version", "occurred_at",
        ]


class AccountabilityTransitionSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    event_type = serializers.CharField(max_length=80)
    normal_state = serializers.CharField(max_length=40, required=False)
    emergency_state = serializers.CharField(
        max_length=40, required=False, allow_null=True, allow_blank=True
    )
    location_code = serializers.CharField(max_length=120, required=False, allow_blank=True)
    expected_destination = serializers.CharField(max_length=160, required=False, allow_blank=True)
    source_domain = serializers.CharField(max_length=64, required=False, default="accountability")
    source_record_id = serializers.UUIDField(required=False, allow_null=True)
    expected_version = serializers.IntegerField(required=False, min_value=1)
    context = serializers.JSONField(required=False)

    def validate(self, attrs):
        if not any(
            key in attrs
            for key in ("normal_state", "emergency_state", "location_code", "expected_destination")
        ):
            raise serializers.ValidationError("At least one projected state field is required.")
        if attrs.get("emergency_state") == "":
            attrs["emergency_state"] = None
        return attrs
