from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
import logging
from .models import (
    School,
    AcademicYear,
    GradeLevel,
    Family,
    Guardian,
    Student,
    Staff,
    UserAccount,
    UserRole,
    Enrollment,
    CrownPermission,
    RolePermission,
)
from .models import LedgerEntry, StudentTuition, TuitionPlan


logger = logging.getLogger(__name__)


@admin.register(School)
class SchoolAdministratorAdmin(admin.ModelAdmin):
    list_display = ("name", "timezone", "is_active")
    search_fields = ("name",)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("school", "name", "start_date", "end_date", "is_current")
    list_filter = ("school", "is_current")
    search_fields = ("name",)


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ("school", "code", "label", "sort_order")
    list_filter = ("school",)
    search_fields = ("code", "label")


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("school", "family_name", "city", "state", "status")
    list_filter = ("school", "status")
    search_fields = ("family_name", "city", "state", "zip_code")


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ("school", "family", "last_name", "first_name", "email", "portal_access", "custody_flag")
    list_filter = ("school", "portal_access", "custody_flag")
    search_fields = ("last_name", "first_name", "email")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("school", "student_number", "last_name", "first_name", "current_grade_level", "status")
    list_filter = ("school", "status", "current_grade_level")
    search_fields = ("student_number", "last_name", "first_name")


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("school", "last_name", "first_name", "email", "role_type", "status")
    list_filter = ("school", "role_type", "status")
    search_fields = ("last_name", "first_name", "email")


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ("school", "email", "is_active", "staff", "guardian")
    list_filter = ("school", "is_active")
    search_fields = ("email",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("school", "user", "role_code")
    list_filter = ("school", "role_code")
    search_fields = ("user__email", "role_code")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("school", "student", "academic_year", "grade_level", "status", "start_date", "end_date")
    list_filter = ("school", "academic_year", "grade_level", "status")
    search_fields = ("student__last_name", "student__first_name", "student__student_number")


@admin.register(CrownPermission)
class CrownPermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "description")
    search_fields = ("code",)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role_code", "permission")
    list_filter = ("role_code",)
    search_fields = ("role_code", "permission__code")
    autocomplete_fields = ("permission",)


# Ensure finance-owned views do not appear under Core
for model in (LedgerEntry, TuitionPlan, StudentTuition):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        logger.debug("Model not registered in admin: %s", model.__name__)


