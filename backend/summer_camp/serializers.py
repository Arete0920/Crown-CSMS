from rest_framework import serializers

from .models import (
    SummerCampAttendance,
    SummerCampBillingLedgerLink,
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
