from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from academics.models import Section as AcademicSection
from academics.models import TeacherAssignment
from academics.models import Term as AcademicTerm
from core.models import Student as CoreStudent, StudentIdentityLink
from households.scoping import get_request_school_id
from crown_api.access_households import resolve_household_access
from crown_api.models_scheduling_core import SectionEnrollment as LegacySectionEnrollment
from crown_api.scoping_students import get_core_student_or_404_for_request
from crown_api.serializers_scheduling import StudentScheduleEnrollmentSerializer
from households.models import Guardian as HouseholdGuardian


def _require_auth_or_401(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )
    return None


def _compat_household_ids(request, school_id):
    """Return household IDs for the supported compatibility/read domain.

    ADR-001 keeps core.Student as the canonical operational student identity.
    households.* remains a supported compatibility/read domain until the
    separately governed tenant-by-tenant identity convergence is complete.
    """
    if not school_id:
        return set()
    return set(
        HouseholdGuardian.objects.filter(
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

    household_ids = _compat_household_ids(request, school_id)
    if not household_ids:
        return qs.none()

    # academics.Enrollment still references households.Student. This is a
    # bounded read-compatibility filter only; it does not redefine student
    # identity authority and performs no identifier remapping.
    return qs.filter(
        enrollments__student__household_id__in=household_ids,
        enrollments__student__is_active=True,
    ).distinct()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def terms_list(request):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)
    school_id = get_request_school_id(request, required=True)

    canonical_qs = AcademicTerm.objects.filter(school_id=school_id).order_by("-start_date", "code")
    if not access.is_staff:
        canonical_qs = canonical_qs.filter(active=True)

    # Legacy scheduling terms have no tenant owner. They cannot be safely
    # enumerated in a shared multi-school deployment. Only canonical terms
    # that belong to the selected school may be returned.
    return Response([_canonical_term_payload(term) for term in canonical_qs])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def term_sections(request, term_id):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)
    school_id = get_request_school_id(request, required=True)

    # Unowned legacy term/section rows cannot be attributed to a school.
    # Resolve from the tenant-owned canonical term table or fail closed.
    canonical_term = get_object_or_404(AcademicTerm, id=term_id, school_id=school_id)
    if canonical_term is not None:
        if not access.is_staff and not canonical_term.active:
            return Response({"detail": "Not found."}, status=404)
        sections = _canonical_sections_for_term(request, canonical_term, access, school_id)
        return Response([_canonical_section_payload(section) for section in sections])



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_schedule(request, student_id):
    """Return the schedule for the canonical core.Student identity.

    The legacy scheduling tables remain an explicitly supported read adapter
    under ADR-001. We deliberately do not treat households.Student UUIDs as
    canonical and do not name/email/position-match identities across domains.
    """
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)
    school_id = get_request_school_id(request, required=True)
    student = get_object_or_404(CoreStudent, id=student_id, school_id=school_id)
    link = StudentIdentityLink.objects.filter(
        school_id=school_id, core_student=student,
        compatibility_student__school_id=school_id,
        compatibility_student__is_active=True,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
    ).exclude(evidence_reference="").first()
    if not access.is_staff and not (link and link.compatibility_student.account_id == request.user.id):
        get_core_student_or_404_for_request(request=request, student_id=student_id)
    if link is not None:
        sections = AcademicSection.objects.filter(
            school_id=school_id, term_ref__school_id=school_id, term_ref__active=True,
            enrollments__school_id=school_id,
            enrollments__student_id=link.compatibility_student_id,
        ).select_related("term_ref", "course").distinct().order_by("term_ref__code", "course__code", "id")
        return Response([_canonical_section_payload(section) for section in sections])

    enrollments = (
        LegacySectionEnrollment.objects.filter(student=student, active=True)
        .select_related("section", "section__term", "section__course", "section__teacher")
        .order_by("section__term__code", "section__course__course_code", "section__section_code")
    )
    return Response(StudentScheduleEnrollmentSerializer(enrollments, many=True).data)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_schedule(request):
    """Published recurring meetings for the authenticated student's or teacher's identity."""
    school_id = get_request_school_id(request, required=True)
    user = request.user
    qs = AcademicSection.objects.filter(school_id=school_id, term_ref__school_id=school_id,
        term_ref__active=True).select_related("term_ref", "course")
    if user.staff_id and user.staff.school_id == school_id and user.staff.status == "ACTIVE":
        qs = qs.filter(teacher_assignments__staff_id=user.staff_id,
                       teacher_assignments__school_id=school_id)
    else:
        student_ids = StudentIdentityLink.objects.filter(
            school_id=school_id, core_student__school_id=school_id,
            compatibility_student__school_id=school_id, compatibility_student__account=user,
            compatibility_student__is_active=True,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
        ).exclude(evidence_reference="").values_list("compatibility_student_id", flat=True)
        qs = qs.filter(enrollments__school_id=school_id, enrollments__student_id__in=student_ids)
    rows = [_canonical_section_payload(section) for section in qs.distinct().order_by("course__code", "id")]
    return Response([row for row in rows if row["meetings"]])
