from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
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
