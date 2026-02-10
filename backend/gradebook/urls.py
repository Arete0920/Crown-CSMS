from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    GradebookSectionViewSet,
    assignments_list,
    section_assignments,
    section_grades,
    section_roster,
    section_summary,
    students_list,
)


router = SimpleRouter()
router.register(r"gradebook/sections", GradebookSectionViewSet, basename="gradebook-sections")

urlpatterns = [
    path("", include(router.urls)),
    path("gradebook/assignments/", assignments_list, name="gradebook-assignments-list"),
    path("gradebook/students/", students_list, name="gradebook-students-list"),
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
]
