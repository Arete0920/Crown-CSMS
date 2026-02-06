from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .assignments_views import (
    assignment_list_create,
    assignment_update_delete,
    category_list_create,
    category_update_delete,
)
from .transcript_views import TranscriptROView
from .views import (
    AcademicYearViewSet,
    CourseViewSet,
    SectionViewSet,
    TermViewSet,
    parent_students,
    student_sections,
)

router = SimpleRouter()
router.register(r"academics/years", AcademicYearViewSet, basename="academics-years")
router.register(r"academics/terms", TermViewSet, basename="academics-terms")
router.register(r"academics/courses", CourseViewSet, basename="academics-courses")
router.register(r"academics/sections", SectionViewSet, basename="academics-sections")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "academics/transcript/<uuid:student_id>/",
        TranscriptROView.as_view(),
        name="transcript-ro",
    ),
    path(
        "academics/students/<uuid:student_id>/sections/",
        student_sections,
        name="academics-student-sections",
    ),
    path(
        "academics/parents/me/students/",
        parent_students,
        name="academics-parent-students",
    ),
    # Assignment Category endpoints
    path(
        "academics/sections/<uuid:section_id>/categories/",
        category_list_create,
        name="section-categories",
    ),
    path(
        "academics/categories/<uuid:category_id>/",
        category_update_delete,
        name="category-detail",
    ),
    # Assignment endpoints
    path(
        "academics/sections/<uuid:section_id>/assignments/",
        assignment_list_create,
        name="section-assignments",
    ),
    path(
        "academics/assignments/<uuid:assignment_id>/",
        assignment_update_delete,
        name="assignment-detail",
    ),
]
