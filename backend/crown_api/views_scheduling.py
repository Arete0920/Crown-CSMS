from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from crown_api.models import Section, SectionEnrollment, Term
from core.models import Student
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_scheduling import (
    StudentScheduleEnrollmentSerializer,
    TermListSerializer,
)


def _require_auth_or_401(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def terms_list(request):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)

    qs = Term.objects.all()
    if not access.is_staff:
        qs = qs.filter(active=True)

    return Response(TermListSerializer(qs.order_by("-start_date", "code"), many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def term_sections(request, term_id):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)

    term_qs = Term.objects.all()
    if not access.is_staff:
        term_qs = term_qs.filter(active=True)

    term = get_object_or_404(term_qs, id=term_id)

    qs = (
        Section.objects.filter(term=term)
        .select_related("term", "course", "teacher")
        .order_by("course__course_code", "section_code")
    )

    if not access.is_staff:
        # Filter sections to only those with in-scope students
        # Get all in-scope student IDs
        from admissions.models import AdmissionsApplication
        in_scope_student_ids = set(
            AdmissionsApplication.objects.filter(
                household_id__in=access.household_ids
            ).values_list("student_id", flat=True)
        )
        qs = qs.filter(
            roster__active=True,
            roster__student_id__in=in_scope_student_ids,
        ).distinct()

    payload = []
    for section in qs:
        payload.append(
            {
                "section_id": str(section.id),
                "term": {"term_id": str(section.term_id), "code": section.term.code, "name": section.term.name},
                "course": {"code": section.course.course_code, "name": section.course.name},
                "section_code": section.section_code,
                "name": section.name_override or section.course.name,
                "teacher": (
                    {
                        "person_id": str(section.teacher_id),
                        "first_name": section.teacher.first_name,
                        "last_name": section.teacher.last_name,
                    }
                    if section.teacher_id
                    else None
                ),
                "room": section.room,
                "meeting_days": section.meeting_days,
                "meeting_time": section.meeting_time,
            }
        )

    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_schedule(request, student_id):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)

    if not access.is_staff:
        # Enforce household-based access control (returns 404 if out of scope)
        get_core_student_or_404_for_request(request=request, student_id=student_id)

    student = get_object_or_404(Student, id=student_id)

    enrollments = (
        SectionEnrollment.objects.filter(student=student, active=True)
        .select_related("section", "section__term", "section__course", "section__teacher")
        .order_by("section__term__code", "section__course__course_code", "section__section_code")
    )

    return Response(StudentScheduleEnrollmentSerializer(enrollments, many=True).data)
