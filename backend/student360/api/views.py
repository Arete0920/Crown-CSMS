from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.views import APIView

from core.models import School, Student as CoreStudent
from crown_api.models import AttendanceRecord
from households.models import Student as HouseholdStudent


def _scope_qs_to_school(qs, model, school):
    """Fail closed unless the model exposes an explicit tenant relationship."""
    if hasattr(model, "school_id"):
        return qs.filter(school_id=str(school.id))
    if hasattr(model, "school"):
        return qs.filter(school=school)
    raise ImproperlyConfigured(
        f"{getattr(model, '__name__', str(model))} must have school_id or school "
        f"for tenant scoping in student360"
    )


def _get_school(request):
    school = getattr(request, "school", None)
    if school:
        return school
    school_id = request.headers.get("X-School-Id")
    if not school_id:
        return None
    try:
        return School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return None


def _get_student(student_id, school):
    """Resolve only an exact same-school ID; never infer cross-family identity."""
    student = CoreStudent.objects.filter(id=student_id, school=school).first()
    if student is not None:
        return student
    return HouseholdStudent.objects.filter(id=student_id, school_id=school.id).first()


def _student_name(student):
    return (
        getattr(student, "full_name", None)
        or (
            f"{getattr(student, 'first_name', '')}".strip()
            + " "
            + f"{getattr(student, 'last_name', '')}".strip()
        ).strip()
        or "Unknown Student"
    )


def _attendance_summary(student):
    """Return canonical AttendanceRecord summary only for canonical core.Student."""
    if not isinstance(student, CoreStudent):
        return {"available": False}

    now = timezone.now()
    since_30 = now.date() - timedelta(days=30)
    records = AttendanceRecord.objects.filter(
        student=student,
        student__school_id=student.school_id,
    )

    last_30 = records.filter(date__gte=since_30)
    last_30_total = last_30.count()
    last_30_present = last_30.filter(status=AttendanceRecord.STATUS_PRESENT).count()

    ytd = records.filter(date__year=now.year)
    ytd_total = ytd.count()
    ytd_present = ytd.filter(status=AttendanceRecord.STATUS_PRESENT).count()

    return {
        "available": True,
        "last30_total": last_30_total,
        "last30_present": last_30_present,
        "last30_pct": round((last_30_present / last_30_total) * 100, 1) if last_30_total else None,
        "ytd_total": ytd_total,
        "ytd_present": ytd_present,
        "ytd_pct": round((ytd_present / ytd_total) * 100, 1) if ytd_total else None,
    }


class StudentOverview(APIView):
    """Internal Student360 assembler; public authorization lives in scoped_views.py."""

    schema = SpectacularAutoSchema()
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, student_id):
        school = _get_school(request)
        if not school:
            return JsonResponse({"detail": "Missing or invalid school context"}, status=400)

        student = _get_student(student_id, school)
        if not student:
            return JsonResponse({"detail": "Student not found"}, status=404)

        attendance = _attendance_summary(student)
        return JsonResponse(
            {
                "student": {
                    "id": str(student.id),
                    "name": _student_name(student),
                    "grade": getattr(student, "grade_level", None),
                },
                "attendance": attendance,
                "finance": {"available": False},
                "discipline": {"available": False},
                "service_hours": {"available": False},
                "comms": {"available": False, "latest_threads": []},
                "dashboard_v2": {
                    "gpa": None,
                    "attendance": attendance,
                    "current_average": None,
                    "missing_assignments": 0,
                    "upcoming_assignments": [],
                    "today_schedule": [],
                    "service_hours": {"available": False, "completed": 0, "required": 30},
                    "financial": {"available": False, "balance_cents": 0},
                    "alerts": [],
                },
            },
            status=200,
            safe=True,
        )
