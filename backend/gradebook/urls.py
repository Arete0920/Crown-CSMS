from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import GradebookSectionViewSet, section_assignments, section_grades, section_roster


router = SimpleRouter()
router.register(r"gradebook/sections", GradebookSectionViewSet, basename="gradebook-sections")

urlpatterns = [
    path("", include(router.urls)),
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
        "gradebook/sections/<uuid:section_id>/grades/",
        section_grades,
        name="gradebook-section-grades",
    ),
]
