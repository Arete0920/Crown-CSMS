from rest_framework import serializers

from .models import (
    AftercareAttendance,
    AftercareEnrollment,
    AftercareIncident,
    AftercarePickupContact,
    AftercareProgramConfig,
)


class _CanonicalSchoolMixin:
    def _request_school(self):
        request = self.context.get("request")
        return getattr(request, "school", None) if request else None

    def validate_student_fk(self, value):
        school = self._request_school()
        if value is not None and school is not None and value.school_id != school.id:
            raise serializers.ValidationError("Student must belong to the requested school.")
        return value


class AftercareProgramConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareProgramConfig
        fields = "__all__"
        read_only_fields = ["school_id", "school_fk"]


class AftercareEnrollmentSerializer(_CanonicalSchoolMixin, serializers.ModelSerializer):
    class Meta:
        model = AftercareEnrollment
        fields = "__all__"
        read_only_fields = ["school_id", "student_id", "school_fk"]
        extra_kwargs = {"student_fk": {"required": True}}


class AftercarePickupContactSerializer(_CanonicalSchoolMixin, serializers.ModelSerializer):
    class Meta:
        model = AftercarePickupContact
        fields = "__all__"
        read_only_fields = ["school_id", "student_id", "school_fk", "student_fk"]


class AftercareAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareAttendance
        fields = "__all__"
        read_only_fields = ["school_id", "student_id", "school_fk", "student_fk"]


class AftercareIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareIncident
        fields = "__all__"
        read_only_fields = ["school_id", "student_id", "school_fk", "student_fk", "discipline_record_id"]
