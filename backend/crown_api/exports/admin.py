from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .models import ExportAuditLog


@admin.register(ExportAuditLog)
class ExportAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "export_name",
        "status_code",
        "school_id",
        "row_count",
        "ip",
    )
    search_fields = (
        "export_name",
        "path",
        "user__username",
        "school_id",
        "ip",
        "user_agent",
    )
    list_filter = (
        "export_name",
        "status_code",
        "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "console/",
                self.admin_site.admin_view(self.export_console_view),
                name="exports_exportauditlog_console",
            ),
        ]
        return custom + urls

    def export_console_view(self, request):
        # last 24 hours by default
        now = timezone.now()
        since = now - timedelta(hours=24)

        qs = ExportAuditLog.objects.filter(created_at__gte=since)

        totals = {
            "total": qs.count(),
            "ok": qs.filter(status_code=200).count(),
            "forbidden": qs.filter(status_code=403).count(),
            "throttled": qs.filter(status_code=429).count(),
            "errors": qs.filter(status_code__gte=500).count(),
        }

        top_exports = qs.values("export_name").annotate(count=Count("id")).order_by("-count")[:10]
        top_users = qs.values("user__username").annotate(count=Count("id")).order_by("-count")[:10]
        top_schools = (
            qs.exclude(school_id="").values("school_id").annotate(count=Count("id")).order_by("-count")[:10]
        )

        recent = qs.select_related("user").order_by("-created_at")[:50]

        context = dict(
            self.admin_site.each_context(request),
            title="Export Console (Last 24 Hours)",
            totals=totals,
            top_exports=list(top_exports),
            top_users=list(top_users),
            top_schools=list(top_schools),
            recent=list(recent),
            since=since,
            now=now,
        )

        return TemplateResponse(request, "admin/exports/export_console.html", context)
