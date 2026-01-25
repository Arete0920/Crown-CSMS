"""
URL configuration for Director APIs

PERSONA-SPECIFIC APIs (per user's spec):
- /api/aid/priority-queue/
- /api/aid/metrics/
- /api/aid/timeline/
- /api/admissions/priority-queue/
- /api/admissions/metrics/
- /api/admissions/timeline/

LEGACY unified APIs (deprecated):
- /api/director/* (returns merged data for all personas)
"""

from django.urls import path, include
from crown_api.director_views import (
    aid_summary,
    finance_summary,
    registrar_summary,
    director_dashboard,
    director_priority,
    director_actions,
    director_timeline,
)
from crown_api.views_households import household_detail, households_list
from crown_api.views_students import student_detail, students_list
from crown_api.views_academics import student_attendance_list, student_grades_list

urlpatterns = [
    # Persona-specific API routes (NEW - per user spec)
    path("aid/", include("aid.api_urls")),
    path("admissions/", include("admissions.api_urls")),

    # Households (Module 4 spine) - read-only
    path("households/", households_list, name="households_list"),
    path("households/<uuid:household_id>/", household_detail, name="household_detail"),

    # Students (SIS Student Core) - read-only
    path("students/", students_list, name="students_list"),
    path("students/<uuid:student_id>/", student_detail, name="student_detail"),

    # Academics (Module 6 spine) - read-only
    path(
        "students/<uuid:student_id>/attendance/",
        student_attendance_list,
        name="student_attendance_list",
    ),
    path(
        "students/<uuid:student_id>/grades/",
        student_grades_list,
        name="student_grades_list",
    ),
    
    # Legacy unified routes (DEPRECATED - kept for backwards compatibility)
    path("director/aid/summary/", aid_summary, name="aid_summary"),
    path("director/finance/summary/", finance_summary, name="finance_summary"),
    path("director/registrar/summary/", registrar_summary, name="registrar_summary"),
    path("director/dashboard/", director_dashboard, name="director_dashboard"),
    path("director/priority/", director_priority, name="director_priority"),
    path("director/actions/", director_actions, name="director_actions"),
    path("director/timeline/", director_timeline, name="director_timeline"),
]
