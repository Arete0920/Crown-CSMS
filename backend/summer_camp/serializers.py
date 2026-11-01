from rest_framework import serializers

from .models import (
    SummerCampAttendance,
    SummerCampBillingLedgerLink,
    SummerCampClub,
    SummerCampClubOffering,
    SummerCampClubSelection,
    SummerCampEnrollment,
    SummerCampFormRequirement,
    SummerCampGroup,
    SummerCampGroupAssignment,
    SummerCampHealthReview,
    SummerCampIncident,
    SummerCampPickupContact,
    SummerCampProgram,
    SummerCampProgramConfig,
    SummerCampSession,
    SummerCampStaffAssignment,
)


class SummerCampProgramConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampProgramConfig
        fields = "__all__"


class SummerCampProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampProgram
        fields = "__all__"


class SummerCampSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampSession
        fields = "__all__"


class SummerCampEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampEnrollment
        fields = "__all__"


class SummerCampFormRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampFormRequirement
        fields = "__all__"


class SummerCampHealthReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampHealthReview
        fields = "__all__"


class SummerCampPickupContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampPickupContact
        fields = "__all__"


class SummerCampAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampAttendance
        fields = "__all__"


class SummerCampGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampGroup
        fields = "__all__"


class SummerCampGroupAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampGroupAssignment
        fields = "__all__"


class SummerCampStaffAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampStaffAssignment
        fields = "__all__"


class SummerCampIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampIncident
        fields = "__all__"


class SummerCampBillingLedgerLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampBillingLedgerLink
        fields = "__all__"


class SummerCampClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummerCampClub
        fields = "__all__"
        read_only_fields = ("school",)


class SummerCampClubOfferingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)

    class Meta:
        model = SummerCampClubOffering
        fields = "__all__"
        read_only_fields = ("school",)


class SummerCampClubSelectionSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="offering.club.name", read_only=True)
    offering_start_time = serializers.TimeField(source="offering.start_time", read_only=True)
    offering_end_time = serializers.TimeField(source="offering.end_time", read_only=True)

    class Meta:
        model = SummerCampClubSelection
        fields = "__all__"
        read_only_fields = ("school",)


class SummerCampClubCreateSerializer(serializers.Serializer):
    code = serializers.SlugField(max_length=72)
    name = serializers.CharField(max_length=160)
    category = serializers.ChoiceField(
        choices=[
            "STEM", "ARTS", "SPORTS", "COOKING", "LEADERSHIP",
            "SERVICE", "FAITH", "READING", "OTHER",
        ],
        default="OTHER",
    )
    description = serializers.CharField(required=False, allow_blank=True)


class SummerCampClubOfferingCreateSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)
    club_id = serializers.IntegerField(min_value=1)
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        allow_empty=False,
        max_length=7,
    )
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    location = serializers.CharField(required=False, allow_blank=True, max_length=120)
    instructor_id = serializers.UUIDField(required=False, allow_null=True)
    capacity = serializers.IntegerField(min_value=1)
    waitlist_capacity = serializers.IntegerField(min_value=0, default=0)
    optional_charge_cents = serializers.IntegerField(min_value=0, default=0)
    status = serializers.ChoiceField(choices=["DRAFT", "PUBLISHED"], default="DRAFT")

    def validate_weekdays(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Weekdays must be unique.")
        return value

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("end_time must be after start_time.")
        return attrs


class SummerCampClubSelectionCreateSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField(min_value=1)
    offering_id = serializers.IntegerField(min_value=1)
