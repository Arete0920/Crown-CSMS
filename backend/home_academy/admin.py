from django.contrib import admin

from .models import (
    FinancialAidRule,
    HomeAcademyEnrollment,
    HomeAcademyProgram,
    Offering,
    OfferingEnrollment,
    TranscriptPostingRule,
)


@admin.register(HomeAcademyProgram)
class HomeAcademyProgramAdmin(admin.ModelAdmin):
    list_display = ("school_id", "public_program_name", "program_type", "is_active", "active_school_year")
    search_fields = ("public_program_name", "active_school_year")
    list_filter = ("program_type", "is_active")


@admin.register(HomeAcademyEnrollment)
class HomeAcademyEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "school_id",
        "student_id",
        "status",
        "school_of_record_status",
        "diploma_eligibility_status",
        "is_active",
    )
    search_fields = ("student_id", "grade_level")
    list_filter = ("status", "school_of_record_status", "diploma_eligibility_status", "is_active")


@admin.register(Offering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = (
        "school_id",
        "title",
        "offering_type",
        "price",
        "min_academic_courses_required",
        "homeschool_seat_cap",
        "active",
    )
    search_fields = ("title", "description", "school_year", "term")
    list_filter = ("offering_type", "active", "credit_bearing", "transcript_eligible", "diploma_track_eligible")


@admin.register(OfferingEnrollment)
class OfferingEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "school_id",
        "student_id",
        "offering",
        "status",
        "eligibility_status",
        "payment_status",
        "form_status",
    )
    search_fields = ("student_id", "offering__title")
    list_filter = ("status", "eligibility_status", "payment_status", "form_status", "roster_status")


@admin.register(FinancialAidRule)
class FinancialAidRuleAdmin(admin.ModelAdmin):
    list_display = ("school_id", "charge_type", "aid_eligible", "esa_eligible", "scholarship_eligible", "active")
    list_filter = ("charge_type", "aid_eligible", "esa_eligible", "scholarship_eligible", "active")


@admin.register(TranscriptPostingRule)
class TranscriptPostingRuleAdmin(admin.ModelAdmin):
    list_display = ("offering", "requires_registrar_approval", "transcript_category", "credit_value", "active")
    search_fields = ("offering__title", "transcript_category", "diploma_requirement_area")
    list_filter = ("requires_registrar_approval", "active")
