from django.contrib import admin

from .models import SandboxEvent, SandboxFeedback, SandboxInvite


@admin.register(SandboxInvite)
class SandboxInviteAdmin(admin.ModelAdmin):
    list_display = ("id", "organization_label", "track", "expires_at", "revoked_at", "last_used_at", "created_at")
    search_fields = ("id", "organization_label")
    list_filter = ("track", "default_guidance", "revoked_at")


@admin.register(SandboxEvent)
class SandboxEventAdmin(admin.ModelAdmin):
    list_display = ("event", "track", "guidance", "persona", "school", "route", "occurred_at")
    search_fields = ("event", "persona", "school", "route")
    list_filter = ("event", "track", "guidance", "persona")


@admin.register(SandboxFeedback)
class SandboxFeedbackAdmin(admin.ModelAdmin):
    list_display = ("rating", "track", "guidance", "persona", "school", "follow_up_requested", "created_at")
    search_fields = ("persona", "school", "scenario", "note")
    list_filter = ("rating", "track", "guidance", "follow_up_requested")
