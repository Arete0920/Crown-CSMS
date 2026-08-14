import uuid
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import Course, Section, Term
from core.models import AcademicYear
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id

from .models import SchedulingWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_VIEW_PERM = [CrownModulePermission("scheduling.view")]
_CONFIGURE_PERM = [CrownModulePermission("scheduling.view", "scheduling.configure")]
_EDIT_PERM = [CrownModulePermission("scheduling.view", "scheduling.edit")]
_PUBLISH_PERM = [CrownModulePermission("scheduling.view", "scheduling.publish")]


class SectionIdentityConflict(Exception):
    pass


def _get_session(session_id, school_id):
    return get_object_or_404(
        SchedulingWizardSession, id=session_id, school__id=school_id
    )


def _parse_decimal(value, field_name, min_val=None, default="0"):
    try:
        d = Decimal(str(value)) if value not in (None, "", "None") else Decimal(default)
    except (InvalidOperation, TypeError):
        return None, f"{field_name} must be a valid number"
    if min_val is not None and d < Decimal(str(min_val)):
        return None, f"{field_name} must be >= {min_val}"
    return d, None


def _parse_uuid(value, field_name):
    try:
        return uuid.UUID(str(value)), None
    except (TypeError, ValueError, AttributeError):
        return None, f"{field_name} must be a valid UUID"


def _term_within_academic_year(term_ref, academic_year):
    if term_ref.start_date and term_ref.start_date < academic_year.start_date:
        return False
    if term_ref.start_date and term_ref.start_date > academic_year.end_date:
        return False
    if term_ref.end_date and term_ref.end_date < academic_year.start_date:
        return False
    if term_ref.end_date and term_ref.end_date > academic_year.end_date:
        return False
    if term_ref.start_date and term_ref.end_date and term_ref.end_date < term_ref.start_date:
        return False
    return True


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_CONFIGURE_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = SchedulingWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_CONFIGURE_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    academic_year_id = request.data.get("academic_year_id")
    term_id = request.data.get("term_id")
    if not academic_year_id:
        return Response({"error": "academic_year_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not term_id:
        return Response({"error": "term_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    academic_year = get_object_or_404(AcademicYear, id=academic_year_id, school_id=school_id)
    term_ref = get_object_or_404(Term, id=term_id, school_id=school_id)
    if term_ref.academic_year_id != academic_year.id:
        return Response(
            {"error": "term_id does not belong to academic_year_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not _term_within_academic_year(term_ref, academic_year):
        return Response(
            {"error": "term_id dates are outside the academic_year_id boundary"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.academic_year = academic_year
    session.term_ref = term_ref
    session.term = term_ref.code
    session.school_year = academic_year.name[:16]
    session.status = SchedulingWizardSession.STATUS_CONFIGURED
    session.save(update_fields=[
        "academic_year",
        "term_ref",
        "term",
        "school_year",
        "status",
        "updated_at",
    ])
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "academic_year_id": str(academic_year.id),
        "term_id": str(term_ref.id),
        "term_code": term_ref.code,
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_CONFIGURE_PERM)
def save_courses(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        SchedulingWizardSession.STATUS_CONFIGURED,
        SchedulingWizardSession.STATUS_COURSES_SAVED,
    ):
        return Response(
            {"error": f"Cannot save courses from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )
    if not session.academic_year_id or not session.term_ref_id:
        return Response({"error": "Session is missing canonical academic year/term identity"}, status=status.HTTP_409_CONFLICT)

    courses_raw = request.data.get("courses")
    if not isinstance(courses_raw, list):
        return Response({"error": "courses must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    if len(courses_raw) == 0:
        return Response({"error": "At least one course is required"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    normalised = []
    seen_codes = set()

    for i, c in enumerate(courses_raw):
        prefix = f"courses[{i}]"
        if not isinstance(c, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        code = (c.get("code") or "").strip().upper()
        if not code:
            errors.append(f"{prefix}: code is required")
            continue
        if code in seen_codes:
            errors.append(f"{prefix}: duplicate course code '{code}'")
            continue
        seen_codes.add(code)

        name = (c.get("name") or "").strip()
        if not name:
            errors.append(f"{prefix}: name is required")
            continue

        department = (c.get("department") or "").strip()
        credits, err = _parse_decimal(c.get("credits", 0), f"{prefix}.credits", min_val=0)
        if err:
            errors.append(err)
            continue

        normalised.append({
            "code": code,
            "name": name,
            "department": department,
            "credits": str(credits),
        })

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.courses_config = normalised
    session.status = SchedulingWizardSession.STATUS_COURSES_SAVED
    session.save(update_fields=["courses_config", "status", "updated_at"])
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "courses_count": len(normalised),
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT_PERM)
def stage_sections(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        SchedulingWizardSession.STATUS_COURSES_SAVED,
        SchedulingWizardSession.STATUS_SECTIONS_STAGED,
    ):
        return Response(
            {"error": f"Cannot stage sections from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )
    if not session.academic_year_id or not session.term_ref_id:
        return Response({"error": "Session is missing canonical academic year/term identity"}, status=status.HTTP_409_CONFLICT)

    sections_raw = request.data.get("sections")
    if not isinstance(sections_raw, list):
        return Response({"error": "sections must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    if len(sections_raw) == 0:
        return Response({"error": "At least one section is required"}, status=status.HTTP_400_BAD_REQUEST)

    valid_course_codes = {c["code"] for c in session.courses_config}
    errors = []
    normalised = []
    seen_section_ids = set()

    for i, s in enumerate(sections_raw):
        prefix = f"sections[{i}]"
        if not isinstance(s, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        course_code = (s.get("course_code") or "").strip().upper()
        if not course_code:
            errors.append(f"{prefix}: course_code is required")
            continue
        if course_code not in valid_course_codes:
            errors.append(
                f"{prefix}: course_code '{course_code}' not in courses_config "
                f"(valid: {sorted(valid_course_codes)})"
            )
            continue

        supplied_id = s.get("section_id")
        if supplied_id:
            section_id, err = _parse_uuid(supplied_id, f"{prefix}.section_id")
            if err:
                errors.append(err)
                continue
        else:
            section_id = uuid.uuid5(session.id, f"{i}:{course_code}")

        section_id_str = str(section_id)
        if section_id_str in seen_section_ids:
            errors.append(f"{prefix}: duplicate section_id '{section_id_str}'")
            continue
        seen_section_ids.add(section_id_str)

        normalised.append({
            "section_id": section_id_str,
            "course_code": course_code,
            "teacher_name": (s.get("teacher_name") or "").strip(),
            "grade_band": (s.get("grade_band") or "").strip(),
        })

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.sections_config = normalised
    session.status = SchedulingWizardSession.STATUS_SECTIONS_STAGED
    session.save(update_fields=["sections_config", "status", "updated_at"])
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "sections_count": len(normalised),
        "sections": normalised,
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PUBLISH_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == SchedulingWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
    if session.status != SchedulingWizardSession.STATUS_SECTIONS_STAGED:
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )
    if not request.data.get("confirm"):
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)
    if not session.academic_year_id or not session.term_ref_id:
        return Response({"error": "Session is missing canonical academic year/term identity"}, status=status.HTTP_409_CONFLICT)

    courses_created = 0
    sections_created = 0
    courses_skipped = 0
    sections_skipped = 0

    try:
        with transaction.atomic():
            locked_session = SchedulingWizardSession.objects.select_for_update().select_related(
                "academic_year", "term_ref"
            ).get(id=session.id, school_id=school_id)
            if locked_session.term_ref.academic_year_id != locked_session.academic_year_id:
                raise SectionIdentityConflict("Session academic year/term identity is inconsistent")
            if not _term_within_academic_year(locked_session.term_ref, locked_session.academic_year):
                raise SectionIdentityConflict("Session term dates are outside the academic year boundary")

            course_map = {}
            for c in locked_session.courses_config:
                matches = list(Course.objects.select_for_update().filter(school_id=school_id, code=c["code"])[:2])
                if len(matches) > 1:
                    raise SectionIdentityConflict(f"Course code '{c['code']}' is ambiguous for this school")
                if matches:
                    obj = matches[0]
                    courses_skipped += 1
                else:
                    obj = Course.objects.create(
                        school_id=school_id,
                        code=c["code"],
                        name=c["name"],
                        department=c.get("department", ""),
                        credits=Decimal(c.get("credits", "0")),
                    )
                    courses_created += 1
                course_map[c["code"]] = obj

            for s in locked_session.sections_config:
                course_obj = course_map.get(s["course_code"])
                if not course_obj:
                    raise SectionIdentityConflict(f"Course '{s['course_code']}' is missing from commit map")
                section_id = uuid.UUID(s["section_id"])
                existing = Section.objects.select_for_update().filter(id=section_id).first()
                if existing:
                    if (
                        existing.school_id != school_id
                        or existing.course_id != course_obj.id
                        or existing.term_ref_id != locked_session.term_ref_id
                    ):
                        raise SectionIdentityConflict(
                            f"section_id '{section_id}' already belongs to a different school/course/term"
                        )
                    sections_skipped += 1
                    continue

                Section.objects.create(
                    id=section_id,
                    school_id=school_id,
                    course=course_obj,
                    term_ref=locked_session.term_ref,
                    term=locked_session.term_ref.code,
                    teacher_name=s.get("teacher_name", ""),
                    grade_band=s.get("grade_band", ""),
                )
                sections_created += 1

            commit_result = {
                "courses_created": courses_created,
                "courses_skipped": courses_skipped,
                "sections_created": sections_created,
                "sections_skipped": sections_skipped,
                "section_ids": [s["section_id"] for s in locked_session.sections_config],
                "academic_year_id": str(locked_session.academic_year_id),
                "term_id": str(locked_session.term_ref_id),
            }
            locked_session.commit_result = commit_result
            locked_session.status = SchedulingWizardSession.STATUS_COMMITTED
            locked_session.save(update_fields=["commit_result", "status", "updated_at"])
    except SectionIdentityConflict as exc:
        return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)

    return Response({
        "session_id": str(session.id),
        "status": SchedulingWizardSession.STATUS_COMMITTED,
        **commit_result,
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_VIEW_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == SchedulingWizardSession.STATUS_VERIFIED:
        return Response({
            "session_id": str(session.id),
            "status": session.status,
            **(session.commit_result or {}),
        })
    if session.status != SchedulingWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    expected_ids = [s["section_id"] for s in session.sections_config]
    actual_ids = {
        str(value)
        for value in Section.objects.filter(
            id__in=expected_ids,
            school_id=school_id,
            term_ref_id=session.term_ref_id,
        ).values_list("id", flat=True)
    }
    missing = sorted(set(expected_ids) - actual_ids)
    if missing:
        return Response(
            {"error": "Committed sections failed canonical verification", "missing_section_ids": missing},
            status=status.HTTP_409_CONFLICT,
        )

    session.status = SchedulingWizardSession.STATUS_VERIFIED
    session.save(update_fields=["status", "updated_at"])

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **(session.commit_result or {}),
    })
