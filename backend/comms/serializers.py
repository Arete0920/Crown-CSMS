from rest_framework import serializers

from .models import NotificationPreference, OutboxMessage


class OutboxMessageSerializer(serializers.ModelSerializer):
    """Read serializer for OutboxMessage — used in admin monitoring views."""

    class Meta:
        model = OutboxMessage
        fields = [
            "id",
            "school_id",
            "channel",
            "to",
            "subject",
            "status",
            "attempts",
            "last_error",
            "next_attempt_at",
            "created_at",
            "sent_at",
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Read/write serializer for per-user notification channel preferences."""

    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "user_id",
            "email_enabled",
            "sms_enabled",
            "teams_enabled",
        ]
