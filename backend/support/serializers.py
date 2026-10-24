"""Bounded inputs; identity, school and lifecycle are server-owned."""

from collections.abc import Mapping

from rest_framework import serializers

from support.models import SupportTicket


class StrictSerializer(serializers.Serializer):
    """Reject unknown fields and non-string text rather than coercing inputs."""

    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            raise serializers.ValidationError(
                {"non_field_errors": ["Expected an object."]}
            )
        if set(data) - set(self.fields):
            raise serializers.ValidationError(
                {"non_field_errors": ["Unsupported fields."]}
            )
        for name, field in self.fields.items():
            if name in data and isinstance(field, serializers.CharField):
                if not isinstance(data[name], str):
                    raise serializers.ValidationError({name: "Expected text."})
        return super().to_internal_value(data)


class TicketCreateSerializer(StrictSerializer):
    """Operational descriptions must exclude secrets and protected records."""

    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=10000)
    priority = serializers.ChoiceField(choices=SupportTicket.PRIORITY_CHOICES)


class TicketResolutionSerializer(StrictSerializer):
    """Require an explicit account of the verified resolution."""

    resolution_summary = serializers.CharField(max_length=2000)


class TicketListSerializer(StrictSerializer):
    """Bound result size while preserving the existing tickets response key."""

    page = serializers.IntegerField(min_value=1, default=1)
    per_page = serializers.IntegerField(min_value=1, max_value=100, default=50)
    status = serializers.ChoiceField(
        choices=["open", "escalated", "closed", "all"],
        required=False,
    )
