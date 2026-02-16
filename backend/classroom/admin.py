from django.contrib import admin
from .models import (
    Classroom,
    ClassroomEnrollment,
    ClassroomAnnouncement,
    ClassroomAssignment,
    ClassroomSeatingChart,
)

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "room", "grade_level", "is_active", "created_at")
    list_filter = ("school", "is_active", "grade_level")
    search_fields = ("name", "room")

admin.site.register(ClassroomEnrollment)
admin.site.register(ClassroomAnnouncement)
admin.site.register(ClassroomAssignment)
admin.site.register(ClassroomSeatingChart)
