from django.contrib import admin
from django.db.models import Sum

from .models import ChartAccount, JournalBatch
from .proxies import FinanceLedgerEntry, FinanceTuitionPlan, FinanceStudentTuition


@admin.register(ChartAccount)
class ChartAccountAdmin(admin.ModelAdmin):
    list_display = ("school", "code", "name", "account_type", "is_active")
    list_filter = ("school", "account_type", "is_active")
    search_fields = ("code", "name")


@admin.register(JournalBatch)
class JournalBatchAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "description", "status", "batch_date", "posted_at")
    list_filter = ("school", "academic_year", "status", "batch_date")
    search_fields = ("description",)


@admin.register(FinanceTuitionPlan)
class FinanceTuitionPlanAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "name", "annual_amount_cents", "is_active")
    list_filter = ("school", "academic_year", "is_active")
    search_fields = ("name",)


@admin.register(FinanceStudentTuition)
class FinanceStudentTuitionAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "student", "annual_amount_cents", "discounts_cents", "net_annual_cents")
    list_filter = ("school", "academic_year")
    search_fields = ("student__last_name", "student__first_name", "student__student_number")


class AmountBandFilter(admin.SimpleListFilter):
    title = "Amount bands"
    parameter_name = "band"

    def lookups(self, request, model_admin):
        return [
            ("big", ">= $10,000"),
            ("mid", "$2,000–$9,999"),
            ("small", "< $2,000"),
            ("credit", "Credits (negative)"),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == "big":
            return queryset.filter(amount_cents__gte=1_000_000)
        if v == "mid":
            return queryset.filter(amount_cents__gte=200_000, amount_cents__lt=1_000_000)
        if v == "small":
            return queryset.filter(amount_cents__gt=0, amount_cents__lt=200_000)
        if v == "credit":
            return queryset.filter(amount_cents__lt=0)
        return queryset


@admin.register(FinanceLedgerEntry)
class FinanceLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "entry_date", "family", "student", "account", "amount_cents", "source", "batch")
    list_filter = ("school", "academic_year", "account", "source", AmountBandFilter)
    search_fields = ("family__family_name", "student__last_name", "student__first_name", "memo")
    ordering = ("-entry_date", "-created_at")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        qs = self.get_queryset(request)
        totals = qs.aggregate(total=Sum("amount_cents"))
        extra_context["finance_totals_cents"] = totals.get("total") or 0
        return super().changelist_view(request, extra_context=extra_context)
