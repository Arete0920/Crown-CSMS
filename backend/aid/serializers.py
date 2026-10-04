"""
Aid DRF Serializers
===================
Minimal, read-safe serializers for the Phase 7.5 admin + family endpoints.

FK fields are exposed as their integer PKs via `*_id` naming conventions built
into DRF's ModelSerializer (source="<field>_id" is automatic via depth=0 + id).
"""

from rest_framework import serializers

from aid.models import (
    AidApplication,
    AidAward,
    AidBudgetTracker,
    AidFinancialLineItem,
    AidFinancialProfile,
    AidHouseholdMember,
    AidPolicy,
)


class AidApplicationSerializer(serializers.ModelSerializer):
    """Read serializer for AidApplication.  Used in admin overview + family portal."""

    class Meta:
        model = AidApplication
        fields = [
            "id",
            "family_id",
            "academic_year_id",
            "status",
            "submitted_at",
            "household_size",
            "income_annual_cents",
            "assets_cents",
            "liabilities_cents",
            "statement_of_faith_score",
            "church_involvement_score",
            "family_values_survey_score",
            "pastoral_reference_score",
            "pog_preassessment_score",
            "notes_internal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AidAwardSerializer(serializers.ModelSerializer):
    """Read serializer for AidAward.  Excludes raw explanation_json unless needed."""

    class Meta:
        model = AidAward
        fields = [
            "id",
            "student_id",
            "academic_year_id",
            "aid_application_id",
            "award_type",
            "awarded_cents",
            "recommended_award_cents",
            "mas_score",
            "mas_modifier_bps",
            "decision_status",
            "decided_at",
            "ledger_entry_id",
            "created_at",
        ]
        read_only_fields = fields


class AidAwardWithExplanationSerializer(AidAwardSerializer):
    """Extended version that includes the engine explanation payload."""

    class Meta(AidAwardSerializer.Meta):
        fields = AidAwardSerializer.Meta.fields + ["explanation_json"]
        read_only_fields = fields


class AidPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AidPolicy
        fields = [
            "id",
            "school_id",
            "academic_year_id",
            "need_income_floor_cents",
            "max_award_percent",
            "min_award_percent",
            "bucket_need_bps",
            "bucket_mission_bps",
            "bucket_marketing_bps",
            "bucket_merit_bps",
            "bucket_hardship_bps",
            "mas_weight_statement_of_faith",
            "mas_weight_church_involvement",
            "mas_weight_family_values",
            "mas_weight_pastoral_reference",
            "mas_weight_pog_preassessment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at"]


class AidBudgetTrackerSerializer(serializers.ModelSerializer):
    remaining_cents = serializers.SerializerMethodField()

    def get_remaining_cents(self, obj) -> int:
        return obj.remaining_cents

    class Meta:
        model = AidBudgetTracker
        fields = [
            "id",
            "school_id",
            "academic_year_id",
            "bucket",
            "allocated_cents",
            "awarded_cents",
            "remaining_cents",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "awarded_cents", "remaining_cents", "updated_at"]


class AidHouseholdMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AidHouseholdMember
        fields = [
            "id", "role", "first_name", "last_name", "relationship",
            "student_id", "lives_in_household", "financially_responsible",
        ]
        read_only_fields = fields


class AidFinancialLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AidFinancialLineItem
        fields = [
            "id", "category", "subcategory", "label", "annual_amount_cents",
            "source_type", "source_reference", "verified", "verified_at", "verified_by_id",
        ]
        read_only_fields = fields


class AidFinancialProfileSerializer(serializers.ModelSerializer):
    totals = serializers.SerializerMethodField()
    household_members = AidHouseholdMemberSerializer(many=True, read_only=True)
    line_items = AidFinancialLineItemSerializer(many=True, read_only=True)

    def get_totals(self, obj):
        return obj.totals()

    class Meta:
        model = AidFinancialProfile
        fields = [
            "id", "school_id", "academic_year_id", "family_id",
            "carried_forward_from_id", "verification_status", "consent_to_reuse",
            "confirmed_at", "confirmed_by_id", "last_verified_at",
            "totals", "household_members", "line_items", "created_at", "updated_at",
        ]
        read_only_fields = fields
