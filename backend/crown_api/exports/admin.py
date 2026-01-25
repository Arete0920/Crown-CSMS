from django.contrib import admin

from .models import ExportAuditLog


@admin.register(ExportAuditLog)
class ExportAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "export_name", "status_code", "school_id", "row_count")
    search_fields = ("export_name", "path", "user__username", "school_id")
    list_filter = ("status_code", "export_name", "created_at")
    ordering = ("-created_at",)
