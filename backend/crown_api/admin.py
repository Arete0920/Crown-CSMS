from django.contrib import admin

from crown_api.models import (
    AttendanceRecord,
    Course,
    CourseEnrollment,
    Household,
    HouseholdMember,
    GradeRecord,
    Invoice,
    Payment,
    Person,
    Student,
    StudentProfile,
    Term,
    UserPersonLink,
    Section,
    SectionEnrollment,
)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone", "created_at")
    search_fields = ("first_name", "last_name", "email")


class HouseholdMemberInline(admin.TabularInline):
    model = HouseholdMember
    extra = 0


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("household_name", "primary_city", "primary_state", "created_at")
    search_fields = ("household_name",)
    inlines = (HouseholdMemberInline, StudentInline)


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = ("household", "person", "role", "is_primary", "created_at")
    list_filter = ("role", "is_primary")
    search_fields = ("household__household_name", "person__first_name", "person__last_name", "person__email")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("person", "household", "grade_level", "active", "created_at")
    list_filter = ("active", "grade_level")
    search_fields = ("person__first_name", "person__last_name", "household__household_name")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student", "student_number", "expected_grad_year")


@admin.register(UserPersonLink)
class UserPersonLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "person")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_code", "name", "term", "active")
    list_filter = ("active", "term")
    search_fields = ("course_code", "name")


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("student__person__last_name", "course__course_code")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "date", "status", "minutes_late")
    list_filter = ("status", "date")
    search_fields = ("student__person__last_name", "course__course_code")


@admin.register(GradeRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "period", "assignment_name", "letter_grade", "posted_at")
    list_filter = ("period",)
    search_fields = ("student__person__last_name", "course__course_code", "assignment_name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("household", "invoice_number", "amount_cents", "status", "due_date")
    list_filter = ("status",)
    search_fields = ("invoice_number", "household__household_name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("household", "payment_reference", "amount_cents", "payment_date")
    search_fields = ("payment_reference", "household__household_name")


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "start_date", "end_date", "active")
    list_filter = ("active",)
    search_fields = ("code", "name")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("term", "course", "section_code", "teacher", "room")
    list_filter = ("term", "course")
    search_fields = ("course__course_code", "term__code", "section_code")


@admin.register(SectionEnrollment)
class SectionEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("section", "student", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("student__person__last_name", "section__course__course_code", "section__term__code")
