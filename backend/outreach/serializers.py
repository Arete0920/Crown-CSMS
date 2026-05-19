from rest_framework import serializers
from .models import (
	PartnerOrganization,
	Opportunity,
	ServiceGoal,
	ServiceLog,
	Badge,
	BadgeAward,
)


class PartnerOrganizationSerializer(serializers.ModelSerializer):
	class Meta:
		model = PartnerOrganization
		fields = [
			"id", "school_id", "name", "website", "email", "phone",
			"address_line1", "address_line2", "city", "state", "postal_code",
			"category", "approved", "notes", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class OpportunitySerializer(serializers.ModelSerializer):
	class Meta:
		model = Opportunity
		fields = [
			"id", "school_id", "partner", "title", "description",
			"location", "start_at", "end_at", "capacity",
			"min_grade", "max_grade", "is_active", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class ServiceGoalSerializer(serializers.ModelSerializer):
	class Meta:
		model = ServiceGoal
		fields = [
			"id", "school_id", "name", "school_year", "grade",
			"program_tag", "required_hours", "due_date", "active",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class ServiceLogSerializer(serializers.ModelSerializer):
	class Meta:
		model = ServiceLog
		fields = [
			"id", "school_id", "participant_type", "student", "user",
			"opportunity", "partner", "service_date", "hours", "description",
			"reflection_prompt", "reflection_text", "status",
			"submitted_at", "reviewed_at", "reviewed_by", "reviewer_notes",
			"external_verifier_name", "external_verifier_email",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class BadgeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Badge
		fields = [
			"id", "school_id", "name", "description",
			"threshold_hours", "active", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class BadgeAwardSerializer(serializers.ModelSerializer):
	class Meta:
		model = BadgeAward
		fields = [
			"id", "school_id", "badge", "student",
			"awarded_at", "awarded_by", "note",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "awarded_at", "created_at", "updated_at"]
