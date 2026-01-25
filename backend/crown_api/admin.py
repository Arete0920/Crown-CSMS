from django.contrib import admin

from crown_api.models import Household, HouseholdMember, Person, Student, UserPersonLink


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


@admin.register(UserPersonLink)
class UserPersonLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "person")
