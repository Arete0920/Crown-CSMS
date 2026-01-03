from django.contrib import admin
from .models import ChartAccount, JournalBatch

# TuitionPlan, StudentTuition, LedgerEntry remain in core.admin since they're in core.models


@admin.register(ChartAccount)
class ChartAccountAdmin(admin.ModelAdmin):
    list_display = ('school', 'code', 'name', 'account_type', 'is_active')
    list_filter = ('school', 'account_type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(JournalBatch)
class JournalBatchAdmin(admin.ModelAdmin):
    list_display = ('school', 'academic_year', 'batch_date', 'description', 'status', 'posted_at')
    list_filter = ('school', 'academic_year', 'status', 'batch_date')
    search_fields = ('description',)
    readonly_fields = ('created_at', 'updated_at')
