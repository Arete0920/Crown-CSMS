from django.contrib import admin

from .models import CurriculumCourse, CurriculumUnit, CurriculumLesson


@admin.register(CurriculumCourse)
class CurriculumCourseAdmin(admin.ModelAdmin):
    list_display = ("school", "code", "name", "subject", "grade_level", "is_active")
    list_filter = ("school", "subject", "is_active")
    search_fields = ("code", "name", "subject", "grade_level")


@admin.register(CurriculumUnit)
class CurriculumUnitAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "title", "start_date", "end_date")
    list_filter = ("course__school", "course")
    search_fields = ("course__code", "course__name", "title")


@admin.register(CurriculumLesson)
class CurriculumLessonAdmin(admin.ModelAdmin):
    list_display = ("unit", "order", "title", "planned_date")
    list_filter = ("unit__course__school", "unit__course")
    search_fields = ("unit__course__code", "unit__title", "title")
