from django.contrib import admin

from .forms import (
	DiscountPolicyAdminForm,
	ExtendedCarePolicyAdminForm,
	FinancialAidPolicyAdminForm,
	PaymentPlanPolicyAdminForm,
	TuitionPolicyAdminForm,
)
from .models import (
	DiscountPolicy,
	ExtendedCarePolicy,
	FinancePolicyVersion,
	FinancialAidPolicy,
	PaymentPlanPolicy,
	TuitionPolicy,
)


@admin.register(FinancePolicyVersion)
class FinancePolicyVersionAdmin(admin.ModelAdmin):
	list_display = ("school_id", "academic_year", "is_locked", "updated_at")
	list_filter = ("is_locked", "academic_year")
	search_fields = ("school_id", "academic_year")


@admin.register(TuitionPolicy)
class TuitionPolicyAdmin(admin.ModelAdmin):
	form = TuitionPolicyAdminForm


@admin.register(DiscountPolicy)
class DiscountPolicyAdmin(admin.ModelAdmin):
	form = DiscountPolicyAdminForm


@admin.register(FinancialAidPolicy)
class FinancialAidPolicyAdmin(admin.ModelAdmin):
	form = FinancialAidPolicyAdminForm


@admin.register(PaymentPlanPolicy)
class PaymentPlanPolicyAdmin(admin.ModelAdmin):
	form = PaymentPlanPolicyAdminForm


@admin.register(ExtendedCarePolicy)
class ExtendedCarePolicyAdmin(admin.ModelAdmin):
	form = ExtendedCarePolicyAdminForm
