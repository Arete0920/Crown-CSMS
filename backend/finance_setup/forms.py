from django import forms

from .models import (
	DiscountPolicy,
	ExtendedCarePolicy,
	FinancialAidPolicy,
	PaymentPlanPolicy,
	TuitionPolicy,
)


def _require_non_negative(value: int, field_name: str) -> int:
	if value < 0:
		raise forms.ValidationError(f"{field_name} must be greater than or equal to 0.")
	return value


class TuitionPolicyAdminForm(forms.ModelForm):
	class Meta:
		model = TuitionPolicy
		fields = "__all__"

	def clean_flat_annual_tuition_cents(self):
		value = self.cleaned_data["flat_annual_tuition_cents"]
		return _require_non_negative(value, "flat_annual_tuition_cents")


class DiscountPolicyAdminForm(forms.ModelForm):
	class Meta:
		model = DiscountPolicy
		fields = "__all__"

	def clean_max_discount_percent_bp(self):
		value = self.cleaned_data["max_discount_percent_bp"]
		if value < 0 or value > 10000:
			raise forms.ValidationError("max_discount_percent_bp must be between 0 and 10000.")
		return value


class FinancialAidPolicyAdminForm(forms.ModelForm):
	class Meta:
		model = FinancialAidPolicy
		fields = "__all__"

	def clean_application_fee_cents(self):
		value = self.cleaned_data["application_fee_cents"]
		return _require_non_negative(value, "application_fee_cents")

	def clean_max_aid_per_student_cents(self):
		value = self.cleaned_data["max_aid_per_student_cents"]
		return _require_non_negative(value, "max_aid_per_student_cents")

	def clean_max_aid_per_family_cents(self):
		value = self.cleaned_data["max_aid_per_family_cents"]
		return _require_non_negative(value, "max_aid_per_family_cents")


class PaymentPlanPolicyAdminForm(forms.ModelForm):
	class Meta:
		model = PaymentPlanPolicy
		fields = "__all__"

	def clean_pay_in_full_discount_percent_bp(self):
		value = self.cleaned_data["pay_in_full_discount_percent_bp"]
		if value < 0 or value > 10000:
			raise forms.ValidationError("pay_in_full_discount_percent_bp must be between 0 and 10000.")
		return value

	def clean_late_fee_grace_days(self):
		value = self.cleaned_data["late_fee_grace_days"]
		return _require_non_negative(value, "late_fee_grace_days")

	def clean_late_fee_flat_cents(self):
		value = self.cleaned_data["late_fee_flat_cents"]
		return _require_non_negative(value, "late_fee_flat_cents")


class ExtendedCarePolicyAdminForm(forms.ModelForm):
	class Meta:
		model = ExtendedCarePolicy
		fields = "__all__"

	def clean_late_pickup_grace_minutes(self):
		value = self.cleaned_data["late_pickup_grace_minutes"]
		return _require_non_negative(value, "late_pickup_grace_minutes")

	def clean_late_pickup_fee_cents(self):
		value = self.cleaned_data["late_pickup_fee_cents"]
		return _require_non_negative(value, "late_pickup_fee_cents")

	def clean_late_pickup_per_minute_cents(self):
		value = self.cleaned_data["late_pickup_per_minute_cents"]
		return _require_non_negative(value, "late_pickup_per_minute_cents")
