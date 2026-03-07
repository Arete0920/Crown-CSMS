"""
Academics Dashboard API - Read-only endpoint
Returns enrollment snapshot: student count + sections count
(Attendance data not yet available in spine, using enrollment as proxy)
"""
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from crown_api.dashboards.tenant import get_dashboard_school_id
from academics.models import Section
from households.models import Student


class EnrollmentSnapshotView(APIView):
    """
    GET /api/v1/dashboards/academics/enrollment/

    Returns:
    {
        "school_id": "<uuid>",
        "active_students": 342,
        "active_sections": 48,
        "sections_by_term": [
            {"term": "2026-SPRING", "count": 25},
            {"term": "2026-FALL", "count": 23}
        ]
    }

    Tenant Isolation:
    - Requires X-School-Id header (or user.school_id)
    - Missing tenant → 400 MissingSchoolContext
    - Returns only data for the specified school

    Note: Attendance tracking will be added in future iteration.
    This endpoint provides enrollment summary as Day 2 placeholder.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request, required=True, require_header=True)

        # Count active students
        student_count = Student.objects.filter(school_id=school_id).count()

        # Count sections
        section_qs = Section.objects.filter(school_id=school_id)
        section_count = section_qs.count()

        # Group sections by term
        sections_by_term = list(
            section_qs.values("term")
                     .annotate(count=Count("id"))
                     .order_by("-term")
        )

        return Response({
            "school_id": str(school_id),
            "active_students": student_count,
            "active_sections": section_count,
            "sections_by_term": sections_by_term,
        })
