from django.contrib import admin
from django.db import transaction

from crown_api.audit import audit_log

from .models import MicrosoftIdentityLink, MicrosoftTenantBinding


@admin.register(MicrosoftTenantBinding)
class MicrosoftTenantBindingAdmin(admin.ModelAdmin):
    list_display = ("school", "tenant_id", "display_name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("school__name", "tenant_id", "display_name")

    def get_readonly_fields(self, request, obj=None):
        immutable = ("school", "tenant_id") if obj else ()
        return immutable + ("created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            audit_log(
                request=request,
                action="microsoft.tenant_binding.updated" if change else "microsoft.tenant_binding.created",
                object_type="microsoft_tenant_binding",
                object_id=obj.id,
                school_id=obj.school_id,
                meta={
                    "school_id": str(obj.school_id),
                    "tenant_id": str(obj.tenant_id),
                    "is_active": obj.is_active,
                },
            )


@admin.register(MicrosoftIdentityLink)
class MicrosoftIdentityLinkAdmin(admin.ModelAdmin):
    list_display = ("binding", "user", "object_id", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = (
        "binding__school__name",
        "binding__tenant_id",
        "object_id",
        "user__email",
        "user__username",
    )

    def get_readonly_fields(self, request, obj=None):
        immutable = ("binding", "user", "object_id") if obj else ()
        return immutable + ("created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            audit_log(
                request=request,
                action="microsoft.identity_link.updated" if change else "microsoft.identity_link.created",
                object_type="microsoft_identity_link",
                object_id=obj.id,
                school_id=obj.binding.school_id,
                meta={
                    "school_id": str(obj.binding.school_id),
                    "tenant_id": str(obj.binding.tenant_id),
                    "object_id": str(obj.object_id),
                    "user_id": str(obj.user_id),
                    "is_active": obj.is_active,
                },
            )
