from rest_framework import serializers
from .models import DisciplineIncident, DisciplineAction


class DisciplineActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplineAction
        fields = ["id", "incident", "actor", "action_type", "note", "created_at"]
        read_only_fields = ["id", "created_at"]


class DisciplineIncidentSerializer(serializers.ModelSerializer):
    actions = DisciplineActionSerializer(many=True, read_only=True)

    class Meta:
        model = DisciplineIncident
        fields = [
            "id", "school", "student", "reported_by", "assigned_to",
            "occurred_at", "location", "category", "severity", "status",
            "summary", "details", "parent_notified", "parent_notified_at",
            "created_at", "actions",
        ]
        read_only_fields = ["id", "created_at"]

