# backend/facops/api/serializers.py
from __future__ import annotations

from rest_framework import serializers

from facops.models import (
    Alert,
    Asset,
    Drill,
    Location,
    SafetyIncident,
    VisitorLog,
    WorkOrder,
    WorkOrderComment,
)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "kind", "parent", "notes", "created_at", "updated_at"]


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "asset_tag",
            "location",
            "category",
            "manufacturer",
            "model",
            "serial_number",
            "installed_on",
            "retired_on",
            "notes",
            "created_at",
            "updated_at",
        ]


class WorkOrderCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderComment
        fields = ["id", "work_order", "author", "author_name", "body", "created_at"]

    def get_author_name(self, obj: WorkOrderComment) -> str:
        if obj.author_id and hasattr(obj.author, "get_full_name"):
            return obj.author.get_full_name() or obj.author.username
        return ""


class WorkOrderSerializer(serializers.ModelSerializer):
    comments = WorkOrderCommentSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "category",
            "location",
            "asset",
            "requested_by",
            "assigned_to",
            "due_at",
            "closed_at",
            "labor_minutes",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["requested_by", "closed_at"]


class SafetyIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyIncident
        fields = [
            "id",
            "title",
            "description",
            "severity",
            "location",
            "related_asset",
            "reported_by",
            "assigned_to",
            "occurred_at",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reported_by"]


class DrillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drill
        fields = [
            "id",
            "drill_type",
            "planned_for",
            "started_at",
            "completed_at",
            "notes",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_by"]


class VisitorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorLog
        fields = [
            "id",
            "name",
            "purpose",
            "checked_in_at",
            "checked_out_at",
            "badge_id",
            "external_ref",
        ]


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id",
            "kind",
            "title",
            "body",
            "emitted_by",
            "channel",
            "external_ref",
            "created_at",
        ]
        read_only_fields = ["emitted_by", "external_ref"]
