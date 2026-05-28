from rest_framework import serializers

from .models import (
    FinancialAidRule,
    HomeAcademyEnrollment,
    HomeAcademyProgram,
    Offering,
    OfferingEnrollment,
    TranscriptPostingRule,
)


class HomeAcademyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeAcademyProgram
        fields = "__all__"
        read_only_fields = ["school_id", "created_at", "updated_at"]


class HomeAcademyEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeAcademyEnrollment
        fields = "__all__"
        read_only_fields = ["school_id", "created_at", "updated_at"]


class OfferingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offering
        fields = "__all__"
        read_only_fields = ["school_id", "created_at", "updated_at"]


class OfferingEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferingEnrollment
        fields = "__all__"
        read_only_fields = [
            "school_id",
            "eligibility_status",
            "eligibility_failures",
            "roster_status",
            "created_at",
            "updated_at",
        ]


class FinancialAidRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialAidRule
        fields = "__all__"
        read_only_fields = ["school_id", "created_at", "updated_at"]


class TranscriptPostingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptPostingRule
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class EligibilityResponseSerializer(serializers.Serializer):
    eligible = serializers.BooleanField()
    failures = serializers.ListField(child=serializers.CharField())
    seats_remaining = serializers.IntegerField()
    waitlist_available = serializers.BooleanField()
