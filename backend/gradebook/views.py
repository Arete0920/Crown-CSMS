from django.db.models import Count, F, Max, Q, Sum
from django.db.models.functions import Coalesce
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

    assignments_qs = (
        GradeEntry.objects.filter(section=section, school_id=school_id)
        .select_related("assignment")
        .annotate(
            _assignment_id=F("assignment__id"),
            _assignment_name=Coalesce(F("assignment__name"), F("assignment_name")),
            _points_possible=Coalesce(F("assignment__points_possible"), F("points_possible")),
        )
        .values("_assignment_id", "_assignment_name", "_points_possible")
        .distinct()
        .order_by("_assignment_name")
    )
    assignments = [
        {
            "assignment_id": a["_assignment_id"],
            "assignment_name": a["_assignment_name"],
            "points_possible": a["_points_possible"],
        }
        for a in assignments_qs
    ]

    return Response(
        {
            "section_id": str(section.id),
            "assignments": assignments,
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

    # Count distinct assignments - use assignment_id if available, otherwise fall back to assignment_name
    assignment_count = (
        qs.annotate(_name_fallback=Coalesce(F("assignment__name"), F("assignment_name")))
        .values("_name_fallback")
        .distinct()
        .count()
    )
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

    entries = GradeEntry.objects.filter(section=section, school_id=school_id).select_related("assignment")
    assignments_qs = (
        entries.annotate(
            _assignment_id=F("assignment__id"),
            _assignment_name=Coalesce(F("assignment__name"), F("assignment_name")),
            _points_possible=Coalesce(F("assignment__points_possible"), F("points_possible")),
        )
        .values("_assignment_id", "_assignment_name", "_points_possible")
        .distinct()
        .order_by("_assignment_name")
    )
    assignments = [
        {
            "assignment_id": a["_assignment_id"],
            "assignment_name": a["_assignment_name"],
            "points_possible": a["_points_possible"],
        }
        for a in assignments_qs
    ]

    roster = (
        Enrollment.objects.filter(section=section)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    entry_map = {}
    for entry in entries:
        entry_map[(str(entry.student_id), str(entry.assignment_id))] = {
            "grade_entry_id": str(entry.id),
            "points_earned": entry.points_earned,
            "points_possible": entry.assignment.points_possible if entry.assignment else entry.points_possible,
        }

    rows = []
    for enrollment in roster:
        student = enrollment.student
        scores = {}
        for assignment in assignments:
            key = (str(student.id), str(assignment["assignment_id"]))
            scores[assignment["assignment_name"]] = entry_map.get(
                key,
                {
                    "grade_entry_id": None,
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
            "course_code": section.course.code,
            "course_name": section.course.name,
            "term_code": section.term,
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
    assignments_qs = (
        GradeEntry.objects.filter(school_id=school_id, section_id=section.id)
        .select_related("assignment")
        .annotate(
            _assignment_id=F("assignment__id"),
            _assignment_name=Coalesce(F("assignment__name"), F("assignment_name")),
            _points_possible=Coalesce(F("assignment__points_possible"), F("points_possible")),
        )
        .values("_assignment_id", "_assignment_name", "_points_possible")
        .distinct()
        .order_by("_assignment_name")
    )
    assignments = [
        {
            "assignment_id": a["_assignment_id"],
            "assignment_name": a["_assignment_name"],
            "points_possible": a["_points_possible"],
        }
        for a in assignments_qs
    ]

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_drilldown(request, section_id):
    """
    GET /api/v1/gradebook/sections/<section_id>/drilldown/
    
    Paginated drilldown rows for a section, filtered by bucket (missing|below_threshold|all).
    
    Query params:
    - bucket: 'missing', 'below_threshold', or 'all' (default: 'all')
    - threshold: float (default: 70) – used only when bucket='below_threshold'
    - category_id: UUID (optional, currently not implemented)
    - limit: int (default: 25, max: 200)
    - offset: int (default: 0)
    
    Response shape:
    {
      "section_id": "...",
      "section_name": "...",
      "total": 150,
      "limit": 25,
      "offset": 0,
      "rows": [
        {
          "student_id": "...",
          "student_name": "Last, First",
          "grade_level": "9",
          "category_id": null,
          "category_name": null,
          "total_points_earned": 45,
          "total_points_possible": 50,
          "pct": 90.0,
          "status": "below_threshold|missing|normal",
          "assignments_count": 5,
          "missing_count": 1,
          "late_count": 0,
          "last_submission": "2026-02-09T14:22:00Z"
        }
      ]
    }
    """
    school_id = get_request_school_id(request, required=True)
    section = _get_section_or_404(request, school_id, section_id)

    # Parameters
    bucket = (request.query_params.get("bucket") or "all").strip().lower()
    threshold = float(request.query_params.get("threshold") or 70)
    category_id = request.query_params.get("category_id")  # not used in MVP
    
    try:
        limit = int(request.query_params.get("limit") or 25)
        offset = int(request.query_params.get("offset") or 0)
    except (ValueError, TypeError):
        return Response(
            {"detail": "limit and offset must be integers"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate bounds
    limit = max(1, min(200, limit))
    offset = max(0, offset)

    # Validate bucket
    valid_buckets = ["all", "missing", "below_threshold"]
    if bucket not in valid_buckets:
        return Response(
            {"detail": f"Invalid bucket '{bucket}'. Must be one of: {', '.join(valid_buckets)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Fetch all student-grade aggregates for this section
    enrollments = (
        Enrollment.objects.filter(section=section)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    # Compute per-student aggregates
    rows_data = []
    for enrollment in enrollments:
        student = enrollment.student
        entries = GradeEntry.objects.filter(
            section=section, student=student, school_id=school_id
        )

        # Count assignments and missing entries
        total_entries = entries.count()
        missing_count = entries.filter(points_earned__isnull=True).count()

        # Compute total points (only non-missing)
        scored = entries.filter(points_earned__isnull=False)
        sums = scored.aggregate(
            earned=Sum("points_earned"),
            possible=Sum("points_possible"),
            updated=Max("updated_at"),
        )

        earned = float(sums["earned"] or 0)
        possible = float(sums["possible"] or 0)
        pct = (earned / possible * 100) if possible > 0 else 0
        last_submission = sums["updated"]

        # Determine status
        status_val = "normal"
        if missing_count > 0:
            status_val = "missing"
        elif pct < threshold:
            status_val = "below_threshold"

        rows_data.append(
            {
                "student_id": str(student.id),
                "student_name": f"{student.last_name}, {student.first_name}".strip(),
                "grade_level": student.grade_level,
                "category_id": None,
                "category_name": None,
                "total_points_earned": round(earned, 2),
                "total_points_possible": round(possible, 2),
                "pct": round(pct, 1),
                "status": status_val,
                "assignments_count": total_entries,
                "missing_count": missing_count,
                "late_count": 0,
                "last_submission": last_submission.isoformat() if last_submission else None,
            }
        )

    # Apply bucket filter
    if bucket == "missing":
        rows_data = [r for r in rows_data if r["missing_count"] > 0]
    elif bucket == "below_threshold":
        rows_data = [r for r in rows_data if r["pct"] < threshold]

    total_count = len(rows_data)

    # Apply pagination
    paginated_rows = rows_data[offset : offset + limit]

    payload = {
        "section_id": str(section.id),
        "section_name": section.course.name if section.course else "",
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "rows": paginated_rows,
    }

    return Response(payload)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_grade_entry(request, entry_id):
    """
    PATCH /api/v1/gradebook/grade-entries/{entry_id}/
    
    Update points_earned for a specific grade entry.
    
    Tenant-scoped: must include X-School-Id header matching entry's school_id.
    
    Request:
      {"points_earned": 95}
    
    Returns updated entry or 400/403/404.
    """
    school_id = get_request_school_id(request, required=True)

    entry = get_object_or_404(
        GradeEntry,
        id=entry_id,
        school_id=school_id,
    )

    from .serializers import GradeEntryUpdateSerializer

    serializer = GradeEntryUpdateSerializer(
        entry,
        data=request.data,
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
