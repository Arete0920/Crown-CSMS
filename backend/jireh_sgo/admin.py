"""Provision SGO organizations and membership explicitly through platform administration."""
from django.contrib import admin

from .models import SGOOrganization, SGOMembership, SGOProgram, SGOApplication, SGOAward, SGOAuditEvent


@admin.register(SGOOrganization)
class SGOOrganizationAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "state_of_domicile", "active", "federal_listing_verified")
    search_fields = ("legal_name",)


@admin.register(SGOMembership)
class SGOMembershipAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "role", "active")
    list_filter = ("organization", "role", "active")


@admin.register(SGOProgram)
class SGOProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "calendar_year", "funding_source", "status")
    readonly_fields = ("organization", "name", "code", "calendar_year", "funding_source", "eligibility_rule_version", "status")


@admin.register(SGOApplication)
class SGOApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "program", "eligibility")
    readonly_fields = [field.name for field in SGOApplication._meta.fields]


@admin.register(SGOAward)
class SGOAwardAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "amount_cents", "status")
    readonly_fields = [field.name for field in SGOAward._meta.fields]


@admin.register(SGOAuditEvent)
class SGOAuditEventAdmin(admin.ModelAdmin):
    list_display = ("organization", "action", "happened_at")
    readonly_fields = [field.name for field in SGOAuditEvent._meta.fields]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
