"""Read-only serializers for SOLOMON governance and context APIs."""

from __future__ import annotations

from rest_framework import serializers

from .models import (
	SolomonAudience,
	SolomonCategory,
	SolomonContextRule,
	SolomonPlaybook,
	SolomonResource,
	SolomonResourceVersion,
	SolomonTopic,
)
from .permissions import can_view_restricted_solomon_content


class SolomonCategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = SolomonCategory
		fields = ("id", "name", "slug", "description", "sort_order", "is_public")
		read_only_fields = fields


class SolomonTopicSerializer(serializers.ModelSerializer):
	class Meta:
		model = SolomonTopic
		fields = ("id", "name", "slug", "description")
		read_only_fields = fields


class SolomonAudienceSerializer(serializers.ModelSerializer):
	class Meta:
		model = SolomonAudience
		fields = ("id", "name", "slug", "role_code", "description", "is_public")
		read_only_fields = fields


class SolomonResourceVersionSerializer(serializers.ModelSerializer):
	resource_slug = serializers.CharField(source="resource.slug", read_only=True)

	class Meta:
		model = SolomonResourceVersion
		fields = (
			"id",
			"resource_slug",
			"version",
			"title",
			"summary",
			"change_note",
			"created_at",
		)
		read_only_fields = fields


class SolomonResourceSerializer(serializers.ModelSerializer):
	category = serializers.SerializerMethodField()
	topics = SolomonTopicSerializer(many=True, read_only=True)
	audiences = serializers.SerializerMethodField()

	class Meta:
		model = SolomonResource
		fields = (
			"id",
			"title",
			"slug",
			"summary",
			"resource_type",
			"status",
			"visibility",
			"scope",
			"category",
			"topics",
			"audiences",
			"owner",
			"approver",
			"review_date",
			"version",
			"license_type",
			"source_url",
			"module",
			"route_path",
			"sort_order",
			"created_at",
			"updated_at",
		)
		read_only_fields = fields

	def get_category(self, obj):
		request = self.context.get("request")
		if obj.category is None:
			return None
		if can_view_restricted_solomon_content(request) or obj.category.is_public:
			return SolomonCategorySerializer(obj.category, context=self.context).data
		return None

	def get_audiences(self, obj):
		request = self.context.get("request")
		audiences = obj.audiences.all()
		if not can_view_restricted_solomon_content(request):
			audiences = audiences.filter(is_public=True)
		return SolomonAudienceSerializer(audiences, many=True, context=self.context).data


class SolomonPlaybookSerializer(serializers.ModelSerializer):
	category = serializers.SerializerMethodField()
	audiences = serializers.SerializerMethodField()

	class Meta:
		model = SolomonPlaybook
		fields = (
			"id",
			"title",
			"slug",
			"summary",
			"module",
			"category",
			"visibility",
			"status",
			"route_path",
			"checklist",
			"audiences",
			"owner",
			"approver",
			"review_date",
			"version",
			"sort_order",
			"created_at",
			"updated_at",
		)
		read_only_fields = fields

	def get_category(self, obj):
		request = self.context.get("request")
		if obj.category is None:
			return None
		if can_view_restricted_solomon_content(request) or obj.category.is_public:
			return SolomonCategorySerializer(obj.category, context=self.context).data
		return None

	def get_audiences(self, obj):
		request = self.context.get("request")
		audiences = obj.audiences.all()
		if not can_view_restricted_solomon_content(request):
			audiences = audiences.filter(is_public=True)
		return SolomonAudienceSerializer(audiences, many=True, context=self.context).data


class SolomonContextRuleSerializer(serializers.ModelSerializer):
	resource = SolomonResourceSerializer(read_only=True)
	playbook = SolomonPlaybookSerializer(read_only=True)
	audience = SolomonAudienceSerializer(read_only=True)

	class Meta:
		model = SolomonContextRule
		fields = (
			"id",
			"module",
			"route_path",
			"context_key",
			"resource",
			"playbook",
			"audience",
			"priority",
			"is_active",
			"created_at",
			"updated_at",
		)
		read_only_fields = fields


class SolomonContextResponseSerializer(serializers.Serializer):
	module = serializers.CharField()
	route = serializers.CharField()
	audience = serializers.CharField(allow_blank=True, required=False)
	scope = serializers.CharField(allow_blank=True, required=False)
	resources = SolomonResourceSerializer(many=True)
	guides = SolomonResourceSerializer(many=True)
	playbooks = SolomonPlaybookSerializer(many=True)
	context_help = SolomonContextRuleSerializer(many=True)
