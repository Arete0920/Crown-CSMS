from __future__ import annotations

from core.audit_mixins import AuditMutationMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AcademicYear, UserRole
from core.viewsets import TenantScopedViewSet
from households.models import Guardian, Student
from households.scoping import get_request_school_id

from .models import AssignmentCategory, Course, Enrollment, Section, Term, Assignment
from .models import CurriculumSource, Unit, Lesson, PublisherObjective, Submission, Grade, MasteryRecord, TranscriptEntry
from .serializers import (
    AcademicYearSerializer,
    CourseSerializer,
    SectionDetailSerializer,
    SectionListSerializer,
    SectionRosterStudentSerializer,
    SectionSerializer,
    StudentSerializer,
    TermSerializer,
    CurriculumSourceSerializer,
    UnitSerializer,
    LessonSerializer,
    PublisherObjectiveSerializer,
    SubmissionSerializer,
    SubmissionCreateSerializer,
    GradeSerializer,
    GradeCreateSerializer,
    MasteryRecordSerializer,
    TranscriptEntrySerializer,
)


def _student_display_name(student: Student) -> str:
    first = getattr(student, "first_name", "") or ""
    last = getattr(student, "last_name", "") or ""
    return " ".join(part for part in [first, last] if part).strip()


def _parse_pagination(request) -> tuple[int, int]:
    try:
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
    except ValueError:
        raise ValidationError("limit and offset must be integers")

    if limit < 1 or limit > 200 or offset < 0:
        raise ValidationError("limit must be 1..200 and offset must be >= 0")

    return limit, offset


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    user_id = getattr(user, "id", None)
    if not user_id:
        return set()
    return set(
        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list("role_code", flat=True)
    )


def _is_staffish(user, roles: set[str]) -> bool:
    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or ("HEAD_OF_SCHOOL" in roles)
    )


def _guardian_household_ids_for_user(user, school_id) -> set:
    email = (getattr(user, "email", None) or "").strip()
    if not email:
        return set()
    return set(
        Guardian.objects.filter(school_id=school_id, email__iexact=email).values_list(
            "household_id", flat=True
        )
    )


def _sections_for_access(request, school_id):
    user = getattr(request, "user", None)
    roles = _role_codes(user, school_id)

    qs = (
        Section.objects.filter(school_id=school_id)
        .select_related("course", "term_ref")
        .annotate(roster_count=Count("enrollments", distinct=True))
    )

    if _is_staffish(user, roles):
        return qs

    if "TEACHER" in roles:
        staff = getattr(user, "staff", None)
        if not staff:
            return qs.none()
        return qs.filter(teacher_assignments__staff=staff).distinct()

    if "PARENT" in roles:
        household_ids = _guardian_household_ids_for_user(user, school_id)
        if not household_ids:
            return qs.none()
        student_ids = Student.objects.filter(
            school_id=school_id, household_id__in=household_ids
        ).values_list("id", flat=True)
        return qs.filter(enrollments__student_id__in=student_ids).distinct()

    if "STUDENT" in roles:
        return qs.none()

    raise PermissionDenied("Role not permitted for academics endpoints.")


def _assert_student_in_scope_or_404(request, school_id, student_id) -> None:
    user = getattr(request, "user", None)
    roles = _role_codes(user, school_id)

    if _is_staffish(user, roles):
        if not Student.objects.filter(pk=student_id, school_id=school_id).exists():
            raise Http404()
        return

    if "TEACHER" in roles:
        staff = getattr(user, "staff", None)
        if not staff:
            raise Http404()
        if not Enrollment.objects.filter(
            student_id=student_id,
            section__school_id=school_id,
            section__teacher_assignments__staff=staff,
        ).exists():
            raise Http404()
        return

    if "PARENT" in roles:
        household_ids = _guardian_household_ids_for_user(user, school_id)
        if not household_ids:
            raise Http404()
        if not Student.objects.filter(
            pk=student_id, school_id=school_id, household_id__in=household_ids
        ).exists():
            raise Http404()
        return

    if "STUDENT" in roles:
        raise PermissionDenied("Student identity mapping not configured.")

    raise PermissionDenied("Role not permitted for academics endpoints.")


class PaginatedReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()
        limit, offset = _parse_pagination(request)
        page = qs[offset : offset + limit]
        serializer = self.get_serializer(page, many=True)
        return Response(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": serializer.data,
            }
        )


class AcademicYearViewSet(PaginatedReadOnlyViewSet):
    serializer_class = AcademicYearSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = AcademicYear.objects.filter(school_id=school_id).order_by("start_date")
        if _is_staffish(user, roles):
            return qs

        sections = _sections_for_access(self.request, school_id)
        term_year_ids = Term.objects.filter(sections__in=sections).values_list(
            "academic_year_id", flat=True
        )
        return qs.filter(id__in=term_year_ids).distinct()


class TermViewSet(PaginatedReadOnlyViewSet):
    serializer_class = TermSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = Term.objects.filter(school_id=school_id).order_by("ordering", "code")

        academic_year_id = self.request.query_params.get("academic_year") or self.request.query_params.get(
            "academic_year_id"
        )
        school_year = self.request.query_params.get("school_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if school_year:
            qs = qs.filter(school_year=school_year)

        if _is_staffish(user, roles):
            return qs

        sections = _sections_for_access(self.request, school_id)
        return qs.filter(sections__in=sections).distinct()


class CourseViewSet(PaginatedReadOnlyViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = Course.objects.filter(school_id=school_id).order_by("code")

        academic_year_id = self.request.query_params.get("academic_year") or self.request.query_params.get(
            "academic_year_id"
        )
        term_id = self.request.query_params.get("term_id")
        term_code = self.request.query_params.get("term")

        if academic_year_id:
            qs = qs.filter(sections__term_ref__academic_year_id=academic_year_id)
        if term_id:
            qs = qs.filter(sections__term_ref_id=term_id)
        if term_code:
            qs = qs.filter(sections__term=term_code)

        if _is_staffish(user, roles):
            return qs.distinct()

        sections = _sections_for_access(self.request, school_id)
        return qs.filter(sections__in=sections).distinct()


class SectionViewSet(PaginatedReadOnlyViewSet):
    """
    Read-only Sections.

    Filters (query params):
      - academic_year / academic_year_id : UUID (filters term_ref__academic_year_id)
      - term_id                          : UUID (filters term_ref_id)
      - term                             : str  (filters term code)
      - student_id                       : UUID (filters enrollments__student_id)
      - teacher_id                       : UUID (filters teacher_assignments__staff_id)

    Role guard:
      - TEACHER may only query teacher_id matching their own staff id.
    """
    serializer_class = SectionListSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SectionDetailSerializer
        return SectionListSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = _sections_for_access(self.request, school_id)

        academic_year_id = self.request.query_params.get("academic_year") or self.request.query_params.get(
            "academic_year_id"
        )
        term_id = self.request.query_params.get("term_id")
        term_code = self.request.query_params.get("term")
        student_id = self.request.query_params.get("student_id")
        teacher_id = self.request.query_params.get("teacher_id")

        if academic_year_id:
            qs = qs.filter(term_ref__academic_year_id=academic_year_id)
        if term_id:
            qs = qs.filter(term_ref_id=term_id)
        if term_code:
            qs = qs.filter(term=term_code)
        if student_id:
            qs = qs.filter(enrollments__student_id=student_id)
        if teacher_id:
            qs = qs.filter(teacher_assignments__staff_id=teacher_id)

        if "TEACHER" in roles and teacher_id:
            staff = getattr(user, "staff", None)
            if not staff or str(staff.id) != str(teacher_id):
                return qs.none()

        # Deterministic ordering (stable for UI + tests)
        qs = qs.order_by(
            "term_ref__academic_year__start_date",
            "term_ref__ordering",
            "term",
            "course__name",
            "id",
        )
        return qs.distinct()

    @action(detail=True, methods=["get"])
    def roster(self, request, pk=None):
        """
        GET /api/v1/academics/sections/{pk}/roster/

        Returns section metadata + teacher + enrolled students.
        Students ordered deterministically: last_name, first_name, student_id.

        Response shape:
        {
          "section_id": "...",
          "section_name": "...",
          "course_code": "...",
          "term": { "id": "...", "name": "..." },
          "teacher": { "id": "...", "name": "...", "email": "..." } or null,
          "students": [ { "student_id": "...", "name": "...", "grade_level": "...", "enrollment_status": "active" } ],
          "counts": { "students": <count> }
        }
        """
        school_id = get_request_school_id(request, required=True)
        section = (
            _sections_for_access(request, school_id)
            .select_related("course", "term_ref", "teacher")
            .filter(id=pk)
            .first()
        )
        if not section:
            raise Http404()

        # Fetch enrollments and students, deterministically ordered
        enrollments = (
            Enrollment.objects.filter(school_id=school_id, section_id=section.id)
            .select_related("student")
            .order_by("student__last_name", "student__first_name", "student__id")
        )

        students = [
            {
                "student_id": str(e.student.id),
                "name": f"{e.student.last_name}, {e.student.first_name}",
                "grade_level": e.student.grade_level,
                "enrollment_status": "active",
            }
            for e in enrollments
        ]

        # Resolve teacher (nullable)
        teacher = None
        if section.teacher:
            teacher = {
                "id": str(section.teacher.id),
                "name": section.teacher.get_full_name(),
                "email": section.teacher.email,
            }

        # Resolve term (nullable)
        term = None
        if section.term_ref:
            term = {
                "id": str(section.term_ref.id),
                "name": section.term_ref.name,
            }

        payload = {
            "section_id": str(section.id),
            "section_name": section.course.name if section.course else "",
            "course_code": section.course.code if section.course else "",
            "term": term,
            "teacher": teacher,
            "students": students,
            "counts": {
                "students": len(students),
            },
        }

        return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_sections(request, student_id):
    school_id = get_request_school_id(request, required=True)
    _assert_student_in_scope_or_404(request, school_id, student_id)

    qs = _sections_for_access(request, school_id).filter(enrollments__student_id=student_id).distinct()
    serializer = SectionSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parent_students(request):
    school_id = get_request_school_id(request, required=True)
    user = getattr(request, "user", None)
    roles = _role_codes(user, school_id)

    if _is_staffish(user, roles):
        qs = Student.objects.filter(school_id=school_id).order_by("last_name", "first_name")
        return Response(StudentSerializer(qs, many=True).data)

    if "PARENT" not in roles:
        raise PermissionDenied("Parent role required for this endpoint.")

    household_ids = _guardian_household_ids_for_user(user, school_id)
    if not household_ids:
        return Response([])

    qs = Student.objects.filter(school_id=school_id, household_id__in=household_ids).order_by(
        "last_name", "first_name"
    )
    return Response(StudentSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_assessments(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _sections_for_access(request, school_id).filter(id=section_id).first()
    if not section:
        raise Http404()

    categories = (
        AssignmentCategory.objects
        .filter(school_id=school_id, section_id=section.id)
        .order_by("sort_order", "name")
    )

    items = []
    for category in categories:
        items.append({
            "section_id": str(section.id),
            "category": category.name,
            "weight": str(category.weight_percent),
            "published": category.is_active,
        })

    return Response({
        "section_id": str(section.id),
        "assessments": items,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_roster(request, section_id):
    """
    GET /api/v1/academics/sections/<section_id>/roster/

    Returns section metadata + teacher + enrolled students (deterministic order).

    Tenant-scoped and role-filtered via _sections_for_access.
    Students ordered by: last_name, first_name, student_id (stable).
    """
    school_id = get_request_school_id(request, required=True)
    section = (
        _sections_for_access(request, school_id)
        .select_related("course", "term_ref", "teacher")
        .filter(id=section_id)
        .first()
    )
    if not section:
        raise Http404()

    # Fetch enrollments and students, deterministically ordered
    enrollments = (
        Enrollment.objects
        .select_related("student")
        .filter(section=section, school_id=school_id)
        .order_by("student__last_name", "student__first_name", "student__id")
    )

    students = [
        {
            "student_id": str(e.student.id),
            "name": f"{e.student.last_name}, {e.student.first_name}",
            "grade_level": e.student.grade_level,
            "enrollment_status": "active",
        }
        for e in enrollments
    ]

    # Resolve teacher (nullable)
    teacher = None
    if section.teacher:
        teacher = {
            "id": str(section.teacher.id),
            "name": section.teacher.get_full_name(),
            "email": section.teacher.email,
        }

    # Resolve term (nullable)
    term = None
    if section.term_ref:
        term = {
            "id": str(section.term_ref.id),
            "name": section.term_ref.name,
        }

    payload = {
        "section_id": str(section.id),
        "section_name": section.name or "",
        "course_code": section.course.code if section.course else "",
        "term": term,
        "teacher": teacher,
        "students": students,
        "counts": {
            "students": len(students),
        },
    }

    return Response(payload)


# =============================================================================
# CURRICULUM VIEWSETS
# =============================================================================


class CurriculumSourceViewSet(PaginatedReadOnlyViewSet):
    serializer_class = CurriculumSourceSerializer
    queryset = CurriculumSource.objects.order_by("name")

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        return self.queryset.filter(school_id=school_id).order_by("name")


class UnitViewSet(PaginatedReadOnlyViewSet):
    serializer_class = UnitSerializer
    queryset = Unit.objects.select_related("course", "curriculum_source").all()

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        qs = self.queryset.filter(school_id=school_id)

        # Filter by course if provided
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)

        return qs.order_by("course__code", "sequence_order")


class LessonViewSet(PaginatedReadOnlyViewSet):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.select_related("unit", "unit__course").all()

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        qs = self.queryset.filter(school_id=school_id)

        # Filter by unit if provided
        unit_id = self.request.query_params.get("unit_id")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)

        return qs.order_by("lesson_date", "title")


class PublisherObjectiveViewSet(PaginatedReadOnlyViewSet):
    serializer_class = PublisherObjectiveSerializer
    queryset = PublisherObjective.objects.select_related("lesson", "lesson__unit").all()

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        qs = self.queryset.filter(school_id=school_id)

        # Filter by lesson if provided
        lesson_id = self.request.query_params.get("lesson_id")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)

        return qs.order_by("objective_code")


# =============================================================================
# SUBMISSION & GRADE VIEWSETS
# =============================================================================


class SubmissionViewSet(TenantScopedViewSet):
    """
    Writable ViewSet for student submissions.
    Inherits tenant scoping from TenantScopedViewSet.
    """
    queryset = Submission.objects.select_related(
        "assignment", "enrollment", "enrollment__student"
    ).all()

    def get_serializer_class(self):
        if self.action in ("create",):
            return SubmissionCreateSerializer
        return SubmissionSerializer

    def get_queryset(self):
        qs = super().get_queryset()  # school scoping handled by base class

        # Filter by assignment if provided
        assignment_id = self.request.query_params.get("assignment_id")
        if assignment_id:
            qs = qs.filter(assignment_id=assignment_id)

        # Filter by student if provided
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(enrollment__student_id=student_id)

        return qs.order_by("-submitted_at")


class GradeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GradeSerializer
    queryset = Grade.objects.select_related(
        "submission", "submission__assignment", "graded_by"
    ).all()

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        qs = self.queryset.filter(school_id=school_id)

        # Filter by submission if provided
        submission_id = self.request.query_params.get("submission_id")
        if submission_id:
            qs = qs.filter(submission_id=submission_id)

        return qs.order_by("-graded_at")

    @action(detail=False, methods=["post"], url_path="grade")
    def grade_submission(self, request):
        """
        Grade a submission.
        POST /api/academics/grades/grade/
        Body: {submission_id, numeric_score, teacher_feedback}
        """
        from .services import upsert_grade_for_submission
        from decimal import Decimal

        ser = GradeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        submission_id = ser.validated_data["submission_id"]
        numeric_score: Decimal = ser.validated_data["numeric_score"]
        feedback = ser.validated_data.get("teacher_feedback", "")

        submission = get_object_or_404(
            Submission.objects.select_related("assignment"),
            id=submission_id
        )

        # Verify school_id matches
        school_id = get_request_school_id(request)
        if submission.school_id != school_id:
            raise PermissionDenied("Submission not in your school")

        grade = upsert_grade_for_submission(
            submission=submission,
            numeric_score=numeric_score,
            graded_by=request.user,
            feedback=feedback
        )

        return Response(GradeSerializer(grade).data)


# =============================================================================
# MASTERY & TRANSCRIPT VIEWSETS
# =============================================================================


class MasteryRecordViewSet(PaginatedReadOnlyViewSet):
    serializer_class = MasteryRecordSerializer
    queryset = MasteryRecord.objects.select_related(
        "student", "objective", "evidence_assignment"
    ).all()

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        qs = self.queryset.filter(school_id=school_id)

        # Filter by student if provided
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)

        # Filter by objective if provided
        objective_id = self.request.query_params.get("objective_id")
        if objective_id:
            qs = qs.filter(objective_id=objective_id)

        return qs.order_by("-last_demonstrated_at")


class TranscriptEntryViewSet(PaginatedReadOnlyViewSet):
    serializer_class = TranscriptEntrySerializer
    queryset = TranscriptEntry.objects.select_related(
        "student", "course", "term"
    ).all()

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        qs = self.queryset.filter(school_id=school_id)

        # Filter by student if provided
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)

        return qs.order_by("term__ordering", "course__code")
