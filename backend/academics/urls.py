from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .assignments_views import (
    assignment_list_create,
    assignment_update_delete,
    category_batch_weights,
    category_list_create,
    category_update_delete,
)
from .transcript_views import StudentTranscriptContractView, TranscriptROView
from .views import (
    AcademicYearViewSet,
    CourseViewSet,
    SectionViewSet,
    TermViewSet,
    parent_students,
    section_assessments,
    section_roster,
    student_sections,
    CurriculumSourceViewSet,
    UnitViewSet,
    LessonViewSet,
    PublisherObjectiveViewSet,
    SubmissionViewSet,
    GradeViewSet,
    MasteryRecordViewSet,
    TranscriptEntryViewSet,
)

router = SimpleRouter()
router.include_format_suffixes = False
router.register(r"academics/years", AcademicYearViewSet, basename="academics-years")
router.register(r"academics/terms", TermViewSet, basename="academics-terms")
router.register(r"academics/courses", CourseViewSet, basename="academics-courses")
router.register(r"academics/sections", SectionViewSet, basename="academics-sections")

# Curriculum endpoints
router.register(r"academics/curriculum-sources", CurriculumSourceViewSet, basename="curriculum-sources")
router.register(r"academics/units", UnitViewSet, basename="units")
router.register(r"academics/lessons", LessonViewSet, basename="lessons")
router.register(r"academics/objectives", PublisherObjectiveViewSet, basename="objectives")

# Submission & Grade endpoints
router.register(r"academics/submissions", SubmissionViewSet, basename="submissions")
router.register(r"academics/grades", GradeViewSet, basename="grades")

# Mastery & Transcript endpoints
router.register(r"academics/mastery", MasteryRecordViewSet, basename="mastery")
router.register(r"academics/transcript-entries", TranscriptEntryViewSet, basename="transcript-entries")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "academics/transcript/<uuid:student_id>/",
        TranscriptROView.as_view(),
        name="transcript-ro",
    ),
    path(
        "transcripts/students/<uuid:student_id>/",
        TranscriptROView.as_view(),
        name="transcript-ro-alias",
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
    path(
        "academics/sections/<uuid:section_id>/assessments/",
        section_assessments,
        name="academics-section-assessments",
    ),
    path(
        "academics/sections/<uuid:section_id>/roster/",
        section_roster,
        name="academics-section-roster",
    ),
    path(
        "academics/students/<uuid:student_id>/transcript/",
        StudentTranscriptContractView.as_view(),
        name="academics-student-transcript",
    ),
    # Assignment Category endpoints
    path(
        "academics/sections/<uuid:section_id>/categories/",
        category_list_create,
        name="section-categories",
    ),
    path(
        "academics/sections/<uuid:section_id>/categories/weights/",
        category_batch_weights,
        name="section-category-weights",
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
