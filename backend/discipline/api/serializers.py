from __future__ import annotations
from rest_framework import serializers
from discipline.models import DisciplineIncident, DisciplineAction

class DisciplineActionSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = DisciplineAction
        fields = ["id", "action_type", "note", "actor_name", "created_at"]

    def get_actor_name(self, obj):
        if not obj.actor:
            return None
        return getattr(obj.actor, "get_full_name", lambda: str(obj.actor))() or str(obj.actor)

class DisciplineIncidentListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = DisciplineIncident
        fields = ["id", "occurred_at", "category", "severity", "status", "summary", "student_name", "parent_notified"]

    def get_student_name(self, obj):
        # Try common patterns without assuming exact model fields
        for attr in ["full_name", "name"]:
            if hasattr(obj.student, attr):
                return getattr(obj.student, attr)
        first = getattr(obj.student, "first_name", "")
        last = getattr(obj.student, "last_name", "")
        name = (first + " " + last).strip()
        return name or str(obj.student_id)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("include_restricted", False):
            data.pop("parent_notified", None)
        return data

class DisciplineIncidentDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    actions = DisciplineActionSerializer(many=True, read_only=True)

    class Meta:
        model = DisciplineIncident
        fields = [
            "id","occurred_at","location","category","severity","status",
            "summary","details","parent_notified","parent_notified_at",
            "student","student_name","reported_by","assigned_to","actions","created_at"
        ]
        read_only_fields = ["created_at"]

    def get_student_name(self, obj):
        for attr in ["full_name", "name"]:
            if hasattr(obj.student, attr):
                return getattr(obj.student, attr)
        first = getattr(obj.student, "first_name", "")
        last = getattr(obj.student, "last_name", "")
        name = (first + " " + last).strip()
        return name or str(obj.student_id)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get("include_restricted", False):
            return data
        for field in ("details", "parent_notified", "parent_notified_at", "reported_by", "assigned_to", "actions"):
            data.pop(field, None)
        return data

class DisciplineActionCreateSerializer(serializers.Serializer):
    action_type = serializers.ChoiceField(choices=["note","assigned","parent_notified","status_changed","closed"])
    note = serializers.CharField(required=False, allow_blank=True)
    assigned_to = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=["open","investigating","closed"], required=False)
