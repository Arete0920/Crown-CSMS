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


class AftercareEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareEnrollment
        fields = "__all__"


class AftercarePickupContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercarePickupContact
        fields = "__all__"


class AftercareAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareAttendance
        fields = "__all__"


class AftercareIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareIncident
        fields = "__all__"
