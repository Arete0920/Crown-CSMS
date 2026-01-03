from django.contrib import admin
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
    TuitionPlan,
    StudentTuition,
    LedgerEntry,
    AidApplication,
    AidDocument,
    AidReview,
    AidAward,
    AidAuditEvent,
)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
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


@admin.register(TuitionPlan)
class TuitionPlanAdmin(admin.ModelAdmin):
    list_display = ("school", "academic_year", "name", "annual_amount_cents", "is_active")
    list_filter = ("school", "academic_year", "is_active")
    search_fields = ("name",)


@admin.register(StudentTuition)
class StudentTuitionAdmin(admin.ModelAdmin):
    list_display = ("school", "student", "academic_year", "annual_amount_cents", "discounts_cents", "net_annual_cents")
    list_filter = ("school", "academic_year")
    search_fields = ("student__student_number", "student__last_name")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("school", "family", "student", "entry_date", "account", "amount_cents", "source", "batch", "is_reversal")
    list_filter = ("school", "academic_year", "account", "source", "entry_date", "is_reversal")
    search_fields = ("family__family_name", "student__student_number", "memo", "account__code")
    readonly_fields = ("created_by_user",)


@admin.register(AidApplication)
class AidApplicationAdmin(admin.ModelAdmin):
    list_display = ("school", "family", "academic_year", "status", "household_size", "income_annual_cents", "submitted_at")
    list_filter = ("school", "academic_year", "status", "submitted_at")
    search_fields = ("family__family_name",)


@admin.register(AidDocument)
class AidDocumentAdmin(admin.ModelAdmin):
    list_display = ("school", "aid_application", "doc_type", "received", "received_at")
    list_filter = ("school", "doc_type", "received")
    search_fields = ("aid_application__family__family_name",)


@admin.register(AidReview)
class AidReviewAdmin(admin.ModelAdmin):
    list_display = ("school", "aid_application", "reviewer_user", "started_at", "completed_at", "recommendation_cents")
    list_filter = ("school", "started_at", "completed_at")
    search_fields = ("aid_application__family__family_name", "reviewer_user__email")
    readonly_fields = ("started_at",)


@admin.register(AidAward)
class AidAwardAdmin(admin.ModelAdmin):
    list_display = ("school", "student", "academic_year", "award_type", "awarded_cents", "decision_status", "decided_at")
    list_filter = ("school", "academic_year", "award_type", "decision_status")
    search_fields = ("student__student_number", "student__last_name")
    readonly_fields = ("decided_by_user", "decided_at")


@admin.register(AidAuditEvent)
class AidAuditEventAdmin(admin.ModelAdmin):
    list_display = ("school", "entity_type", "action", "actor_user", "timestamp")
    list_filter = ("school", "entity_type", "action", "timestamp")
    search_fields = ("actor_user__email", "entity_id")
    readonly_fields = ("timestamp", "details_json")
