from django.db.models import Count, Max, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import UserRole
from households.scoping import get_request_school_id

from academics.models import Enrollment, Section, TeacherAssignment
from academics.serializers import SectionSerializer, StudentSerializer
from academics.views import PaginatedReadOnlyViewSet

from .models import GradeEntry
from .serializers import GradebookAssignmentSerializer, GradebookStudentSerializer


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        UserRole.objects.filter(user=user, school_id=school_id).values_list("role_code", flat=True)
    )


def _is_staffish(user, roles: set[str]) -> bool:
    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or ("HEAD_OF_SCHOOL" in roles)
    )


def _sections_for_gradebook(request, school_id):
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

    raise PermissionDenied("Role not permitted for gradebook endpoints.")


def _get_section_or_404(request, school_id, section_id):
    qs = _sections_for_gradebook(request, school_id)
    if not qs.filter(id=section_id).exists():
        raise Http404()
    return get_object_or_404(Section, id=section_id, school_id=school_id)


class GradebookSectionViewSet(PaginatedReadOnlyViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SectionSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        return _sections_for_gradebook(self.request, school_id).order_by("term", "course__code")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_roster(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _get_section_or_404(request, school_id, section_id)

    enrollments = (
        Enrollment.objects.filter(section=section)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )
    students = [e.student for e in enrollments]
    serializer = StudentSerializer(students, many=True)

    return Response(
        {
            "section_id": str(section.id),
            "students": serializer.data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_assignments(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _get_section_or_404(request, school_id, section_id)

    assignments = (
        GradeEntry.objects.filter(section=section, school_id=school_id)
        .values("assignment_name", "points_possible")
        .distinct()
        .order_by("assignment_name")
    )

    return Response(
        {
            "section_id": str(section.id),
            "assignments": list(assignments),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_summary(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _get_section_or_404(request, school_id, section_id)

    # students (roster size)
    student_count = Enrollment.objects.filter(section=section).count()

    # grade entries scoped to tenant + section
    qs = GradeEntry.objects.filter(section=section, school_id=school_id)

    assignment_count = qs.values("assignment_name").distinct().count()
    missing_count = qs.filter(points_earned__isnull=True).count()

    # class average percent (only non-missing)
    scored = qs.filter(points_earned__isnull=False)
    sums = scored.aggregate(
        earned=Sum("points_earned"),
        possible=Sum("points_possible"),
        updated=Max("updated_at"),
        created=Max("created_at"),
    )

    earned = sums["earned"] or 0
    possible = sums["possible"] or 0
    avg_pct = round((earned / possible) * 100, 2) if possible else None

    last_updated = sums["updated"] or sums["created"]

    return Response(
        {
            "section_id": str(section.id),
            "student_count": student_count,
            "assignment_count": assignment_count,
            "missing_count": missing_count,
            "class_average_pct": avg_pct,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_grades(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _get_section_or_404(request, school_id, section_id)

    entries = GradeEntry.objects.filter(section=section, school_id=school_id)
    assignments = list(
        entries.values("assignment_name", "points_possible")
        .distinct()
        .order_by("assignment_name")
    )

    roster = (
        Enrollment.objects.filter(section=section)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    entry_map = {}
    for entry in entries:
        entry_map[(str(entry.student_id), entry.assignment_name)] = {
            "points_earned": entry.points_earned,
            "points_possible": entry.points_possible,
        }

    rows = []
    for enrollment in roster:
        student = enrollment.student
        scores = {}
        for assignment in assignments:
            key = (str(student.id), assignment["assignment_name"])
            scores[assignment["assignment_name"]] = entry_map.get(
                key,
                {
                    "points_earned": None,
                    "points_possible": assignment.get("points_possible"),
                },
            )
        rows.append(
            {
                "student": {
                    "student_id": str(student.id),
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "grade_level": student.grade_level,
                },
                "scores": scores,
            }
        )

    return Response(
        {
            "section_id": str(section.id),
            "assignments": assignments,
            "rows": rows,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assignments_list(request):
    """
    GET /api/v1/gradebook/assignments/?section_id=<uuid>
    Same auth rules as section_assignments, but query-param based.
    """
    school_id = get_request_school_id(request, required=True)
    section_id = request.query_params.get("section_id")
    if not section_id:
        return Response({"detail": "section_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    section = _get_section_or_404(request, school_id, section_id)

    # Mirror the existing per-section assignments logic.
    # If you already have a helper that computes assignments, call it here.
    assignments = (
        GradeEntry.objects.filter(school_id=school_id, section_id=section.id)
        .values("assignment_name", "points_possible")
        .distinct()
        .order_by("assignment_name")
    )

    return Response(GradebookAssignmentSerializer(assignments, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def students_list(request):
    """
    GET /api/v1/gradebook/students/?section_id=<uuid>
    Same auth rules as section_roster, but query-param based.
    """
    school_id = get_request_school_id(request, required=True)
    section_id = request.query_params.get("section_id")
    if not section_id:
        return Response({"detail": "section_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    section = _get_section_or_404(request, school_id, section_id)

    # Read-only MVP roster: students appearing in GradeEntry for this section.
    students = (
        GradeEntry.objects.filter(school_id=school_id, section_id=section.id)
        .select_related("student")
        .values("student_id", "student__first_name", "student__last_name")
        .distinct()
        .order_by("student__last_name", "student__first_name")
    )

    return Response(GradebookStudentSerializer(students, many=True).data)
