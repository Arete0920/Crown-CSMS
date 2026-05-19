from rest_framework import serializers
from .models import (
	Location, Asset, WorkOrder, WorkOrderComment,
	SafetyIncident, Drill, VisitorLog, Alert,
)


class LocationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Location
		fields = ["id", "school", "name", "kind", "parent", "notes", "created_at", "updated_at"]
		read_only_fields = ["id", "created_at", "updated_at"]


class AssetSerializer(serializers.ModelSerializer):
	class Meta:
		model = Asset
		fields = [
			"id", "school", "name", "asset_tag", "location", "category",
			"manufacturer", "model", "serial_number",
			"installed_on", "retired_on", "notes", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class WorkOrderCommentSerializer(serializers.ModelSerializer):
	class Meta:
		model = WorkOrderComment
		fields = ["id", "school", "work_order", "author", "body", "created_at", "updated_at"]
		read_only_fields = ["id", "created_at", "updated_at"]


class WorkOrderSerializer(serializers.ModelSerializer):
	comments = WorkOrderCommentSerializer(many=True, read_only=True)

	class Meta:
		model = WorkOrder
		fields = [
			"id", "school", "title", "description", "status", "priority",
			"category", "location", "asset", "requested_by", "assigned_to",
			"due_at", "closed_at", "labor_minutes", "created_at", "updated_at",
			"comments",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class SafetyIncidentSerializer(serializers.ModelSerializer):
	class Meta:
		model = SafetyIncident
		fields = [
			"id", "school", "title", "description", "severity",
			"location", "related_asset", "reported_by", "assigned_to",
			"occurred_at", "resolved_at", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class DrillSerializer(serializers.ModelSerializer):
	class Meta:
		model = Drill
		fields = [
			"id", "school", "drill_type", "planned_for",
			"started_at", "completed_at", "notes", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class VisitorLogSerializer(serializers.ModelSerializer):
	class Meta:
		model = VisitorLog
		fields = [
			"id", "school", "name", "purpose",
			"checked_in_at", "checked_out_at", "badge_id", "external_ref",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at", "checked_in_at"]


class AlertSerializer(serializers.ModelSerializer):
	class Meta:
		model = Alert
		fields = [
			"id", "school", "kind", "title", "body",
			"emitted_by", "channel", "external_ref",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]
