from rest_framework import serializers

from outreach.models import (
    PartnerOrganization,
    Opportunity,
    ServiceLog,
    ServiceGoal,
    ReflectionPrompt,
    Badge,
    BadgeAward,
)


class PartnerOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerOrganization
        fields = [
            "id", "name", "website", "email", "phone",
            "address_line1", "address_line2", "city", "state", "postal_code",
            "category", "approved", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OpportunitySerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            "id", "partner", "partner_name", "title", "description", "location",
            "start_at", "end_at", "capacity", "min_grade", "max_grade", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "partner_name"]


class ReflectionPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReflectionPrompt
        fields = ["id", "title", "prompt", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ServiceLogSerializer(serializers.ModelSerializer):
    opportunity_title = serializers.CharField(source="opportunity.title", read_only=True)
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceLog
        fields = [
            "id", "participant_type", "student", "student_name", "user",
            "opportunity", "opportunity_title", "partner", "partner_name",
            "service_date", "hours", "description",
            "reflection_prompt", "reflection_text",
            "status", "submitted_at", "reviewed_at", "reviewed_by", "reviewer_notes",
            "external_verifier_name", "external_verifier_email",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "submitted_at", "reviewed_at", "reviewed_by", "created_at", "updated_at",
            "opportunity_title", "partner_name", "student_name",
        ]

    def get_student_name(self, obj):
        if obj.student_id:
            return f"{obj.student.first_name} {obj.student.last_name}"
        return None

    def validate(self, attrs):
        opportunity = attrs.get("opportunity") or getattr(self.instance, "opportunity", None)
        partner = attrs.get("partner") or getattr(self.instance, "partner", None)
        if opportunity and partner and opportunity.partner_id != partner.id:
            raise serializers.ValidationError(
                "Opportunity partner does not match selected partner."
            )
        return attrs


class ServiceGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceGoal
        fields = [
            "id", "name", "school_year", "grade", "program_tag",
            "required_hours", "due_date", "active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "id", "name", "description", "threshold_hours", "active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BadgeAwardSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source="badge.name", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = BadgeAward
        fields = [
            "id", "badge", "badge_name", "student", "student_name",
            "awarded_at", "awarded_by", "note",
        ]
        read_only_fields = ["id", "awarded_at", "badge_name", "student_name", "awarded_by"]

    def get_student_name(self, obj):
        if obj.student_id:
            return f"{obj.student.first_name} {obj.student.last_name}"
        return None
