from django.contrib import admin
from .models import BoardPacket, BoardReportSnapshot


@admin.register(BoardReportSnapshot)
class BoardReportSnapshotAdmin(admin.ModelAdmin):
    list_display = ("school_id", "as_of_date", "period_label", "created_at")
    list_filter = ("as_of_date", "period_label")
    search_fields = ("school_id", "period_label")


@admin.register(BoardPacket)
class BoardPacketAdmin(admin.ModelAdmin):
    list_display = ("school_id", "title", "meeting_date", "created_at")
    list_filter = ("meeting_date",)
    search_fields = ("title", "school_id")
