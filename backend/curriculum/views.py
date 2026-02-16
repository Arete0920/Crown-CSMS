from __future__ import annotations

from datetime import date

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CurriculumCourse
from .serializers import CurriculumCourseSerializer
from .utils import get_school_from_header


class CurriculumCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only for demo safety.
    """
    serializer_class = CurriculumCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school = get_school_from_header(self.request)
        return (
            CurriculumCourse.objects
            .filter(school=school, is_active=True)
            .prefetch_related("units", "units__lessons")
            .order_by("code", "name")
        )

    def _pacing_summary_for_course(self, course: CurriculumCourse) -> dict:
        """
        Simple pacing:
        - total_lessons: count of all lessons in the course
        - due_lessons: lessons planned on/before today
        - pct_due: due_lessons / total_lessons * 100
        """
        today = date.today()

        agg = (
            course.units
            .values("course_id")
            .annotate(
                total_lessons=Count("lessons", distinct=True),
                due_lessons=Count("lessons", filter=Q(lessons__planned_date__isnull=False, lessons__planned_date__lte=today), distinct=True),
            )
            .order_by("course_id")
        ).first()

        total = int((agg or {}).get("total_lessons") or 0)
        due = int((agg or {}).get("due_lessons") or 0)
        pct = int(round((due / total) * 100)) if total else 0

        return {
            "as_of": str(today),
            "total_lessons": total,
            "due_lessons": due,
            "pct_due": pct,
        }

    @action(detail=True, methods=["get"], url_path="pacing")
    def pacing(self, request, pk=None):
        """
        GET /api/curriculum/courses/{id}/pacing/
        School-scoped via X-School-Id.
        """
        school = get_school_from_header(request)
        course = get_object_or_404(CurriculumCourse, id=pk, school=school, is_active=True)
        return Response({"course_id": str(course.id), "code": course.code, "name": course.name, "pacing": self._pacing_summary_for_course(course)})

    @action(detail=False, methods=["get"], url_path="pacing-summary")
    def pacing_summary(self, request):
        """
        GET /api/curriculum/courses/pacing-summary/
        Returns lightweight pacing for all active courses.
        """
        school = get_school_from_header(request)
        courses = CurriculumCourse.objects.filter(school=school, is_active=True).order_by("code", "name")
        data = []
        for c in courses:
            data.append({
                "course_id": str(c.id),
                "code": c.code,
                "name": c.name,
                "subject": c.subject,
                "grade_level": c.grade_level,
                "pacing": self._pacing_summary_for_course(c),
            })
        return Response({"count": len(data), "results": data})
