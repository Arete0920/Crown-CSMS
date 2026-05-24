from rest_framework import serializers

from .models import (
    DiscountPolicy,
    ExtendedCarePolicy,
    FinancePolicyVersion,
    FinancialAidPolicy,
    PaymentPlanPolicy,
    TuitionPolicy,
)


# ── Individual policy serializers ─────────────────────────────────────────────

class TuitionPolicySerializer(serializers.ModelSerializer):
    flat_annual_tuition_cents = serializers.IntegerField(min_value=0)

    class Meta:
        model = TuitionPolicy
        exclude = ("id", "version")


class DiscountPolicySerializer(serializers.ModelSerializer):
    sibling_discount_percent_bp = serializers.IntegerField(min_value=0, max_value=10000)
    sibling_discount_applies_from_child = serializers.IntegerField(min_value=1)
    staff_discount_percent_bp = serializers.IntegerField(min_value=0, max_value=10000)
    ministry_discount_percent_bp = serializers.IntegerField(min_value=0, max_value=10000)
    max_discount_percent_bp = serializers.IntegerField(min_value=0, max_value=10000)

    class Meta:
        model = DiscountPolicy
        exclude = ("id", "version")


class FinancialAidPolicySerializer(serializers.ModelSerializer):
    application_fee_cents = serializers.IntegerField(min_value=0)
    max_aid_per_student_cents = serializers.IntegerField(min_value=0)
    max_aid_per_family_cents = serializers.IntegerField(min_value=0)

    class Meta:
        model = FinancialAidPolicy
        exclude = ("id", "version")


class PaymentPlanPolicySerializer(serializers.ModelSerializer):
    pay_in_full_discount_percent_bp = serializers.IntegerField(min_value=0, max_value=10000)
    late_fee_grace_days = serializers.IntegerField(min_value=0)
    late_fee_flat_cents = serializers.IntegerField(min_value=0)

    class Meta:
        model = PaymentPlanPolicy
        exclude = ("id", "version")


class ExtendedCarePolicySerializer(serializers.ModelSerializer):
    late_pickup_grace_minutes = serializers.IntegerField(min_value=0)
    late_pickup_fee_cents = serializers.IntegerField(min_value=0)
    late_pickup_per_minute_cents = serializers.IntegerField(min_value=0)

    class Meta:
        model = ExtendedCarePolicy
        exclude = ("id", "version")


class FinancePolicyVersionMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancePolicyVersion
        fields = (
            "id",
            "school_id",
            "academic_year",
            "is_locked",
            "locked_at",
            "locked_by",
            "created_at",
            "updated_at",
        )


# ── Wizard payload (inbound configure POST) ───────────────────────────────────

class FinanceSetupWizardPayloadSerializer(serializers.Serializer):
    academic_year = serializers.RegexField(
        r"^\d{4}-\d{4}$",
        error_messages={"invalid": "academic_year must be YYYY-YYYY format, e.g. 2026-2027"},
    )
    tuition = TuitionPolicySerializer()
    discounts = DiscountPolicySerializer()
    aid = FinancialAidPolicySerializer()
    payment_plans = PaymentPlanPolicySerializer()
    extended_care = ExtendedCarePolicySerializer()


# ── Full snapshot (outbound read) ─────────────────────────────────────────────

class FinancePolicySnapshotSerializer(serializers.Serializer):
    """
    Complete finance policy snapshot returned by /wizard/status/ and /wizard/snapshot/.
    """
    version = FinancePolicyVersionMetaSerializer()
    tuition = TuitionPolicySerializer()
    discounts = DiscountPolicySerializer()
    aid = FinancialAidPolicySerializer()
    payment_plans = PaymentPlanPolicySerializer()
    extended_care = ExtendedCarePolicySerializer()

    def to_representation(self, instance):
        """
        instance is a FinancePolicyVersion with all related objects prefetched.
        We build the shape manually to avoid nested source juggling.
        """
        version_obj = instance
        data = {
            "version": FinancePolicyVersionMetaSerializer(version_obj).data,
        }

        # Each related object may not exist yet if wizard hasn't been configured
        for attr, ser_class in [
            ("tuition", TuitionPolicySerializer),
            ("discounts", DiscountPolicySerializer),
            ("aid", FinancialAidPolicySerializer),
            ("payment_plans", PaymentPlanPolicySerializer),
            ("extended_care", ExtendedCarePolicySerializer),
        ]:
            related = getattr(version_obj, attr, None)
            data[attr] = ser_class(related).data if related else None

        return data
