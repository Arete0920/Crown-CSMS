from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from academics.models import Enrollment as AcademicEnrollment
from academics.models import Section as AcademicSection
from academics.models import TeacherAssignment
from academics.models import Term as AcademicTerm
from core.models import Student as CoreStudent
from crown_api.access_households import resolve_household_access
from crown_api.models_scheduling_core import (
    Section as LegacySection,
    SectionEnrollment as LegacySectionEnrollment,
    Term as LegacyTerm,
)
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_scheduling import StudentScheduleEnrollmentSerializer, TermListSerializer
from households.models import Guardian as CanonicalGuardian
from households.models import Student as CanonicalStudent


def _require_auth_or_401(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )
    return None


def _request_school_id(request):
    school = getattr(request, "school", None)
    if school is not None:
        return school.id
    return getattr(getattr(request, "user", None), "school_id", None)


def _canonical_household_ids(request, school_id):
    if not school_id:
        return set()
    return set(
        CanonicalGuardian.objects.filter(
            school_id=school_id,
            account=request.user,
            household__is_active=True,
        ).values_list("household_id", flat=True)
    )


def _canonical_term_payload(term):
    return {
        "term_id": str(term.id),
        "code": term.code,
        "name": term.name,
        "start_date": term.start_date,
        "end_date": term.end_date,
        "active": term.active,
    }


def _canonical_section_payload(section):
    placements = list(
        section.schedule_placements.filter(is_active=True)
        .select_related("room", "day_template", "period_block")
        .order_by(
            "day_template__ordering",
            "day_template__template_code",
            "period_block__ordering",
            "period_block__start_time",
            "id",
        )
    )
    first_placement = placements[0] if placements else None
    meetings = [
        {
            "placement_id": str(placement.id),
            "day_template_id": str(placement.day_template_id),
            "template_code": placement.day_template.template_code,
            "period_block_id": str(placement.period_block_id),
            "block_code": placement.period_block.code,
            "block_name": placement.period_block.label,
            "start_time": str(placement.period_block.start_time),
            "end_time": str(placement.period_block.end_time),
            "room_id": str(placement.room_id) if placement.room_id else None,
            "room_code": placement.room.code if placement.room_id else "",
        }
        for placement in placements
    ]
    teacher_assignment = (
        TeacherAssignment.objects.filter(section=section)
        .select_related("staff")
        .order_by("staff__last_name", "staff__first_name", "id")
        .first()
    )
    staff = teacher_assignment.staff if teacher_assignment else None

    return {
        "section_id": str(section.id),
        "term": {
            "term_id": str(section.term_ref_id),
            "code": section.term_ref.code,
            "name": section.term_ref.name,
        },
        "course": {"code": section.course.code, "name": section.course.name},
        "section_code": str(section.id),
        "name": section.course.name,
        "teacher": (
            {
                "person_id": None,
                "staff_id": str(staff.id),
                "first_name": staff.first_name,
                "last_name": staff.last_name,
            }
            if staff
            else None
        ),
        "room": first_placement.room.code if first_placement and first_placement.room_id else "",
        "meeting_days": first_placement.day_template.template_code if first_placement else "",
        "meeting_time": first_placement.period_block.label if first_placement else "",
        "meetings": meetings,
    }


def _canonical_sections_for_term(request, term, access, school_id):
    qs = (
        AcademicSection.objects.filter(
            school_id=school_id,
            term_ref=term,
        )
        .select_related("term_ref", "course")
        .order_by("course__code", "id")
    )

    if access.is_staff:
        return qs

    household_ids = _canonical_household_ids(request, school_id)
    if not household_ids:
        return qs.none()

    return qs.filter(
        enrollments__student__household_id__in=household_ids,
        enrollments__student__is_active=True,
    ).distinct()


def _canonical_student_allowed(request, student, access):
    if access.is_staff:
        return True
    if student.account_id == request.user.id:
        return True
    return CanonicalGuardian.objects.filter(
        school_id=student.school_id,
        account=request.user,
        household_id=student.household_id,
    ).exists()


def _canonical_student_schedule_payload(student):
    enrollments = (
        AcademicEnrollment.objects.filter(
            student=student,
            school_id=student.school_id,
        )
        .select_related(
            "section",
            "section__term_ref",
            "section__course",
        )
        .order_by("section__term_ref__code", "section__course__code", "section__id")
    )
    return [_canonical_section_payload(enrollment.section) for enrollment in enrollments]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def terms_list(request):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)
    school_id = _request_school_id(request)

    canonical_qs = AcademicTerm.objects.filter(school_id=school_id).order_by("-start_date", "code")
    if not access.is_staff:
        canonical_qs = canonical_qs.filter(active=True)

    if canonical_qs.exists():
        return Response([_canonical_term_payload(term) for term in canonical_qs])

    legacy_qs = LegacyTerm.objects.order_by("-start_date", "code")
    if not access.is_staff:
        legacy_qs = legacy_qs.filter(active=True)
    return Response(TermListSerializer(legacy_qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def term_sections(request, term_id):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)
    school_id = _request_school_id(request)

    canonical_term = AcademicTerm.objects.filter(id=term_id, school_id=school_id).first()
    if canonical_term is not None:
        if not access.is_staff and not canonical_term.active:
            return Response({"detail": "Not found."}, status=404)
        sections = _canonical_sections_for_term(request, canonical_term, access, school_id)
        return Response([_canonical_section_payload(section) for section in sections])

    legacy_term_qs = LegacyTerm.objects.order_by("-start_date", "code")
    if not access.is_staff:
        legacy_term_qs = legacy_term_qs.filter(active=True)
    legacy_term = get_object_or_404(legacy_term_qs, id=term_id)

    qs = (
        LegacySection.objects.filter(term=legacy_term)
        .select_related("term", "course", "teacher")
        .order_by("course__course_code", "section_code")
    )

    if not access.is_staff:
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
    school_id = _request_school_id(request)

    canonical_student = CanonicalStudent.objects.filter(
        id=student_id,
        school_id=school_id,
        is_active=True,
    ).first()
    if canonical_student is not None:
        if not _canonical_student_allowed(request, canonical_student, access):
            return Response({"detail": "Not found."}, status=404)
        return Response(_canonical_student_schedule_payload(canonical_student))

    if not access.is_staff:
        get_core_student_or_404_for_request(request=request, student_id=student_id)
    student = get_object_or_404(CoreStudent, id=student_id)

    enrollments = (
        LegacySectionEnrollment.objects.filter(student=student, active=True)
        .select_related("section", "section__term", "section__course", "section__teacher")
        .order_by("section__term__code", "section__course__course_code", "section__section_code")
    )
    return Response(StudentScheduleEnrollmentSerializer(enrollments, many=True).data)