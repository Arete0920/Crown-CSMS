"""Admin registration for SOLOMON Phase 2 core knowledge models."""

from django.contrib import admin

from .models import (
    SolomonAudience,
    SolomonCategory,
    SolomonContextRule,
    SolomonPlaybook,
    SolomonResource,
    SolomonResourceVersion,
    SolomonTopic,
)


@admin.register(SolomonCategory)
class SolomonCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_public")
    search_fields = ("name", "slug", "description")
    list_filter = ("is_public",)
    ordering = ("sort_order", "name")
    save_on_top = True


@admin.register(SolomonTopic)
class SolomonTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug", "description")
    ordering = ("name",)
    save_on_top = True


@admin.register(SolomonAudience)
class SolomonAudienceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "role_code", "is_public")
    search_fields = ("name", "slug", "role_code", "description")
    list_filter = ("is_public",)
    ordering = ("name",)
    save_on_top = True


class SolomonResourceVersionInline(admin.TabularInline):
    model = SolomonResourceVersion
    extra = 0
    fields = ("version", "title", "summary", "change_note", "created_at")
    readonly_fields = ("created_at",)


@admin.register(SolomonResource)
class SolomonResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "resource_type",
        "status",
        "visibility",
        "scope",
        "module",
        "updated_at",
    )
    search_fields = ("title", "slug", "summary", "content", "module", "route_path")
    list_filter = ("resource_type", "status", "visibility", "scope", "module")
    list_select_related = ("category",)
    autocomplete_fields = ("category",)
    filter_horizontal = ("topics", "audiences")
    ordering = ("module", "sort_order", "title")
    inlines = (SolomonResourceVersionInline,)
    save_on_top = True


@admin.register(SolomonResourceVersion)
class SolomonResourceVersionAdmin(admin.ModelAdmin):
    list_display = ("resource", "version", "title", "created_at")
    search_fields = ("resource__title", "resource__slug", "version", "title", "change_note")
    list_filter = ("created_at",)
    ordering = ("resource", "-created_at")
    list_select_related = ("resource",)
    save_on_top = True


@admin.register(SolomonPlaybook)
class SolomonPlaybookAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "module", "status", "visibility", "updated_at")
    search_fields = ("title", "slug", "summary", "module", "route_path")
    list_filter = ("status", "visibility", "module")
    list_select_related = ("category",)
    autocomplete_fields = ("category",)
    filter_horizontal = ("audiences",)
    ordering = ("module", "sort_order", "title")
    save_on_top = True


@admin.register(SolomonContextRule)
class SolomonContextRuleAdmin(admin.ModelAdmin):
    list_display = ("module", "route_path", "context_key", "priority", "is_active")
    search_fields = ("module", "route_path", "context_key")
    list_filter = ("module", "is_active")
    list_select_related = ("resource", "playbook", "audience")
    autocomplete_fields = ("resource", "playbook", "audience")
    ordering = ("module", "route_path", "priority")
    save_on_top = True
