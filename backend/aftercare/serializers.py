from rest_framework import serializers
from .models import (
    AftercareProgramConfig,
    AftercareEnrollment,
    AftercarePickupContact,
    AftercareAttendance,
    AftercareIncident,
)


class AftercareProgramConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareProgramConfig
        fields = "__all__"
        read_only_fields = ["school_id"]


class AftercareEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareEnrollment
        fields = "__all__"
        read_only_fields = ["school_id", "school_fk"]

    def validate_student_fk(self, value):
        request = self.context.get("request")
        school = getattr(request, "school", None) if request else None
        if value is not None and school is not None and str(value.school_id) != str(school.id):
            raise serializers.ValidationError("Student must belong to the requested school.")
        return value


class AftercarePickupContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercarePickupContact
        fields = "__all__"
        read_only_fields = ["school_id", "student_id"]


class AftercareAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareAttendance
        fields = "__all__"
        read_only_fields = ["school_id", "school_fk", "student_fk"]


class AftercareIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareIncident
        fields = "__all__"
        read_only_fields = ["school_id", "school_fk", "student_fk"]
