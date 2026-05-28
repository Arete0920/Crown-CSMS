from __future__ import annotations

from rest_framework import serializers

from spiritual_life.formation_models import (
    BiblicalIntegrationRecord,
    BiblicalWorldviewPriority,
    CallingPathwayEvent,
    ChristianEducationSundayCampaign,
    ChurchEngagementEvent,
    ChurchPartner,
    CommunityOrganizationPartner,
    DevotionalContent,
    FamilyFormationEvent,
    FormationArtifact,
    FormationCampaign,
    PastorContact,
    PortraitDomain,
    SpeakerVettingRecord,
    SpiritualCareCase,
    SpiritualDomainRating,
    StaffFormationEvent,
    StudentLeadershipEvent,
    StudentSpiritualLeadershipRole,
)


class PortraitDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortraitDomain
        fields = [
            "id",
            "school_id",
            "name",
            "description",
            "scripture_anchor",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class BiblicalWorldviewPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = BiblicalWorldviewPriority
        fields = [
            "id",
            "school_id",
            "title",
            "scripture_anchor",
            "description",
            "grade_band",
            "school_year",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class FormationCampaignSerializer(serializers.ModelSerializer):
    portrait_domain_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=PortraitDomain.objects.all(),
        source="portrait_domains",
    )
    worldview_priority_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=BiblicalWorldviewPriority.objects.all(),
        source="worldview_priorities",
    )

    class Meta:
        model = FormationCampaign
        fields = [
            "id",
            "school_id",
            "name",
            "theme",
            "scripture_anchor",
            "start_date",
            "end_date",
            "status",
            "owner_id",
            "summary",
            "portrait_domain_ids",
            "worldview_priority_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "owner_id", "created_at", "updated_at"]


class FormationArtifactSerializer(serializers.ModelSerializer):
    portrait_domain_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=PortraitDomain.objects.all(),
        source="portrait_domains",
    )
    worldview_priority_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=BiblicalWorldviewPriority.objects.all(),
        source="worldview_priorities",
    )
    campaign_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=FormationCampaign.objects.all(),
        source="campaigns",
    )

    class Meta:
        model = FormationArtifact
        fields = [
            "id",
            "school_id",
            "artifact_type",
            "title",
            "artifact_date",
            "scripture_reference",
            "summary",
            "evidence_url",
            "created_by_id",
            "campaign_ids",
            "portrait_domain_ids",
            "worldview_priority_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_by_id", "created_at", "updated_at"]


class DevotionalContentSerializer(serializers.ModelSerializer):
    portrait_domain_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=PortraitDomain.objects.all(),
        source="portrait_domains",
    )
    worldview_priority_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=BiblicalWorldviewPriority.objects.all(),
        source="worldview_priorities",
    )

    class Meta:
        model = DevotionalContent
        fields = [
            "id",
            "school_id",
            "title",
            "audience",
            "grade_band",
            "week_number",
            "publish_date",
            "scripture_reference",
            "theme",
            "summary",
            "body",
            "reflection_question",
            "prayer_focus",
            "family_prompt",
            "staff_connection",
            "status",
            "is_published",
            "generated_by_ai",
            "reviewed_by_id",
            "approved_at",
            "portrait_domain_ids",
            "worldview_priority_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "reviewed_by_id", "approved_at", "created_at", "updated_at"]


class BiblicalIntegrationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiblicalIntegrationRecord
        fields = [
            "id",
            "school_id",
            "student_id",
            "grade_label",
            "subject",
            "integration_date",
            "scripture_reference",
            "summary",
            "created_by_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_by_id", "created_at", "updated_at"]


class SpiritualDomainRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpiritualDomainRating
        fields = [
            "id",
            "school_id",
            "student_id",
            "domain_id",
            "rating",
            "rating_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class SpiritualCareCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpiritualCareCase
        fields = [
            "id",
            "school_id",
            "student_id",
            "prayer_request_id",
            "case_type",
            "title",
            "summary",
            "priority",
            "status",
            "owner_id",
            "next_follow_up_date",
            "parent_notified",
            "counselor_referral",
            "admin_review_required",
            "mandated_reporting_concern",
            "outside_referral_made",
            "sensitive",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "owner_id", "created_at", "updated_at"]


class ChurchPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChurchPartner
        fields = [
            "id",
            "school_id",
            "name",
            "denomination",
            "website",
            "address",
            "is_active_partner",
            "relationship_owner_id",
            "partnership_notes",
            "next_follow_up_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "relationship_owner_id", "created_at", "updated_at"]


class PastorContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastorContact
        fields = [
            "id",
            "school_id",
            "church_id",
            "contact_type",
            "name",
            "email",
            "phone",
            "notes",
            "is_primary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class ChurchEngagementEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChurchEngagementEvent
        fields = [
            "id",
            "school_id",
            "church_partner_id",
            "event_type",
            "title",
            "event_date",
            "start_time",
            "location",
            "audience",
            "topic",
            "scripture_reference",
            "speaker_id",
            "materials_needed",
            "school_story_notes",
            "follow_up_notes",
            "follow_up_due",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "speaker_id", "created_at", "updated_at"]


class ChristianEducationSundayCampaignSerializer(serializers.ModelSerializer):
    church_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ChurchPartner.objects.all(),
        source="churches",
    )

    class Meta:
        model = ChristianEducationSundayCampaign
        fields = [
            "id",
            "school_id",
            "name",
            "school_year",
            "campaign_date",
            "theme",
            "scripture_reference",
            "message_summary",
            "owner_id",
            "church_ids",
            "bulletin_insert_ready",
            "slideshow_ready",
            "student_testimony_ready",
            "family_invitation_sent",
            "admissions_follow_up_complete",
            "thank_you_sent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "owner_id", "created_at", "updated_at"]


class CommunityOrganizationPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityOrganizationPartner
        fields = [
            "id",
            "school_id",
            "name",
            "partner_type",
            "contact_name",
            "contact_email",
            "contact_phone",
            "website",
            "relationship_owner_id",
            "partnership_notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "relationship_owner_id", "created_at", "updated_at"]


class StudentSpiritualLeadershipRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSpiritualLeadershipRole
        fields = [
            "id",
            "school_id",
            "student_id",
            "role_type",
            "title",
            "mentor_id",
            "training_completed",
            "parent_permission",
            "testimony_approved",
            "active",
            "start_date",
            "end_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "mentor_id", "created_at", "updated_at"]


class StudentLeadershipEventSerializer(serializers.ModelSerializer):
    attendee_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=StudentLeadershipEvent.attendees.field.remote_field.model.objects.all(),
        source="attendees",
    )

    class Meta:
        model = StudentLeadershipEvent
        fields = [
            "id",
            "school_id",
            "title",
            "event_type",
            "event_date",
            "theme",
            "scripture_reference",
            "facilitator_id",
            "training_objective",
            "follow_up_assignments",
            "attendee_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "facilitator_id", "created_at", "updated_at"]


class CallingPathwayEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallingPathwayEvent
        fields = [
            "id",
            "school_id",
            "title",
            "event_type",
            "event_date",
            "partner_name",
            "representative_name",
            "representative_email",
            "grade_levels_invited",
            "student_interest_count",
            "parent_info_sent",
            "follow_up_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class FamilyFormationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyFormationEvent
        fields = [
            "id",
            "school_id",
            "title",
            "event_date",
            "topic",
            "speaker",
            "resource_url",
            "family_discussion_guide",
            "attendance_count",
            "follow_up_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class StaffFormationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffFormationEvent
        fields = [
            "id",
            "school_id",
            "title",
            "event_type",
            "event_date",
            "scripture_reference",
            "summary",
            "facilitator_id",
            "completion_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "facilitator_id", "created_at", "updated_at"]


class SpeakerVettingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakerVettingRecord
        fields = [
            "id",
            "school_id",
            "speaker_name",
            "organization",
            "affiliation",
            "topic",
            "scripture_reference",
            "grade_appropriateness",
            "statement_of_faith_aligned",
            "parent_sensitive_content",
            "references_checked",
            "reviewer_id",
            "status",
            "review_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "reviewer_id", "created_at", "updated_at"]
