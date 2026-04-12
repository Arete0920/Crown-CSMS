from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    GradebookSectionViewSet,
    assignments_list,
    grade_entry_bulk_upsert,
    section_assignments,
    section_drilldown,
    section_grades,
    section_roster,
    section_summary,
    students_list,
    update_grade_entry,
)
from .views_parent import student_grades_summary


router = SimpleRouter()
router.include_format_suffixes = False
router.register(r"gradebook/sections", GradebookSectionViewSet, basename="gradebook-sections")

urlpatterns = [
    path("", include(router.urls)),
    path("gradebook/assignments/", assignments_list, name="gradebook-assignments-list"),
    path("gradebook/students/", students_list, name="gradebook-students-list"),
    path(
        "gradebook/students/<uuid:student_id>/grades/",
        student_grades_summary,
        name="parent-grades-summary",
    ),
    path(
        "gradebook/sections/<uuid:section_id>/roster/",
        section_roster,
        name="gradebook-section-roster",
    ),
    path(
        "gradebook/sections/<uuid:section_id>/assignments/",
        section_assignments,
        name="gradebook-section-assignments",
    ),
    path(
        "gradebook/sections/<uuid:section_id>/summary/",
        section_summary,
        name="gradebook-section-summary",
    ),
    path(
        "gradebook/sections/<uuid:section_id>/grades/",
        section_grades,
        name="gradebook-section-grades",
    ),
    path(
        "gradebook/sections/<uuid:section_id>/drilldown/",
        section_drilldown,
        name="gradebook-section-drilldown",
    ),
    path(
        "gradebook/grade-entries/<uuid:entry_id>/",
        update_grade_entry,
        name="update-grade-entry",
    ),
    path(
        "gradebook/sections/<uuid:section_id>/assignments/<uuid:assignment_id>/grades/upsert/",
        grade_entry_bulk_upsert,
        name="gradebook-gradeentry-upsert",
    ),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
