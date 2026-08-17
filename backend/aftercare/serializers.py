from rest_framework import serializers

from .models import (
    AftercareAttendance,
    AftercareEnrollment,
    AftercareIncident,
    AftercarePickupContact,
    AftercareProgramConfig,
)


class AftercareProgramConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AftercareProgramConfig
        fields = [
            "id", "start_time", "end_time", "late_fee_per_10_min",
            "late_fee_grace_minutes", "late_fee_cap", "ratio_k_2", "ratio_3_5",
            "ratio_6_8", "ratio_9_12", "default_billing_model", "dropin_daily_rate",
            "prepaid_session_unit_price", "monthly_rate_1_day", "monthly_rate_2_days",
            "monthly_rate_3_days", "monthly_rate_4_days", "monthly_rate_5_days",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AftercareEnrollmentSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student_fk_id")

    class Meta:
        model = AftercareEnrollment
        fields = [
            "id", "student_id", "start_date", "end_date", "days_of_week",
            "billing_model", "monthly_rate", "prepaid_sessions_balance",
            "dropin_daily_rate", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AftercarePickupContactSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student_fk_id", read_only=True)

    class Meta:
        model = AftercarePickupContact
        fields = [
            "id", "student_id", "name", "relationship", "phone", "is_active",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "student_id", "created_at"]


class AftercareAttendanceSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student_fk_id", read_only=True)
    pickup_contact_id = serializers.IntegerField(source="pickup_contact_fk_id", read_only=True, allow_null=True)

    class Meta:
        model = AftercareAttendance
        fields = [
            "id", "student_id", "date", "checkin_time", "checkout_time",
            "pickup_contact_id", "pickup_name_freeform", "pickup_verified",
            "late_minutes", "late_fee_cents", "late_fee_charge_id", "notes", "created_at",
        ]
        read_only_fields = fields


class AftercareIncidentSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student_fk_id", read_only=True)
    attendance_id = serializers.IntegerField(source="attendance_fk_id", read_only=True, allow_null=True)

    class Meta:
        model = AftercareIncident
        fields = [
            "id", "student_id", "attendance_id", "occurred_at", "severity",
            "description", "parent_notified", "discipline_record_id", "created_at",
        ]
        read_only_fields = fields
