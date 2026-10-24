# backend/facops/api/serializers.py
from __future__ import annotations

from rest_framework import serializers

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id

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


class TenantRelatedFieldsMixin:
    """Constrain writable foreign keys to the selected school's records.

    DRF validates PrimaryKeyRelatedField against this queryset before model
    instances are assigned. Never infer school membership from a submitted ID.
    """

    tenant_relation_fields = ()

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        # drf-spectacular constructs a synthetic, unscoped request when
        # generating OpenAPI. Only its explicitly marked fake view may skip
        # tenant selection; ordinary unscoped API requests still fail closed.
        if request is None or getattr(
            self.context.get("view"), "swagger_fake_view", False
        ):
            return fields
        school_id = get_request_school_id(request, required=True)
        for name in self.tenant_relation_fields:
            related = fields.get(name)
            queryset = getattr(related, "queryset", None)
            if queryset is not None:
                related.queryset = queryset.filter(school_id=school_id)
        return fields


class LocationSerializer(TenantRelatedFieldsMixin, serializers.ModelSerializer):
    tenant_relation_fields = ("parent",)
    class Meta:
        model = Location
        fields = ["id", "name", "kind", "parent", "notes", "created_at", "updated_at"]


class AssetSerializer(TenantRelatedFieldsMixin, serializers.ModelSerializer):
    tenant_relation_fields = ("location",)
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
    # Author identity is private when a bypass-written comment references
    # a user from another tenant, even if the comment's school is valid.
    author = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderComment
        fields = ["id", "work_order", "author", "author_name", "body", "created_at"]

    @staticmethod
    def _visible_author(obj: WorkOrderComment):
        author = obj.author if obj.author_id else None
        if author is None or getattr(author, "school_id", None) != obj.school_id:
            return None
        return author

    def get_author(self, obj: WorkOrderComment):
        author = self._visible_author(obj)
        return author.pk if author is not None else None

    def get_author_name(self, obj: WorkOrderComment) -> str:
        author = self._visible_author(obj)
        if author is not None and hasattr(author, "get_full_name"):
            return author.get_full_name() or author.username
        return ""


class WorkOrderSerializer(TenantRelatedFieldsMixin, serializers.ModelSerializer):
    tenant_relation_fields = ("location", "asset", "assigned_to")
    comments = WorkOrderCommentSerializer(many=True, read_only=True)

    def validate(self, attrs):
        """Prevent unauthorized lifecycle writes and cross-school relationships.

        A school member may submit a maintenance request but cannot set its
        status, assignee, due date, labor, or internal priority without the
        explicit school-bound facilities.edit grant.
        """
        request = self.context.get("request")
        if request is None:
            return attrs

        school_id = get_request_school_id(request, required=True)
        for field in ("location", "asset", "assigned_to"):
            related = attrs.get(field)
            if related is not None and getattr(related, "school_id", None) != school_id:
                raise serializers.ValidationError({
                    field: "The selected record is not available for this school."
                })

        view = self.context.get("view")
        if request.method == "POST" and getattr(view, "action", None) == "create":
            school = School.objects.filter(pk=school_id, is_active=True).first()
            may_manage = bool(
                school and user_has_permission(
                    request.user, "facilities.edit", school=school
                )
            )
            if not may_manage:
                restricted = (
                    {"status", "priority", "assigned_to", "due_at", "labor_minutes"}
                    & set(request.data)
                )
                if restricted:
                    raise serializers.ValidationError({
                        field: "A school facilities grant is required."
                        for field in sorted(restricted)
                    })
        return attrs


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


class SafetyIncidentSerializer(TenantRelatedFieldsMixin, serializers.ModelSerializer):
    tenant_relation_fields = ("location", "related_asset", "assigned_to")
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
