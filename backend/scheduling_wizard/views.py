from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import Course, Section
from households.scoping import get_request_school_id

from .models import SchedulingWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
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


# ---------------------------------------------------------------------------
# 2. Configure (term + school_year)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    term = (request.data.get("term") or "").strip()
    if not term:
        return Response({"error": "term is required"}, status=status.HTTP_400_BAD_REQUEST)
    if len(term) > 24:
        return Response({"error": "term must be <= 24 characters"}, status=status.HTTP_400_BAD_REQUEST)

    school_year = (request.data.get("school_year") or "").strip()
    if len(school_year) > 16:
        return Response({"error": "school_year must be <= 16 characters"}, status=status.HTTP_400_BAD_REQUEST)

    session.term = term
    session.school_year = school_year
    session.status = SchedulingWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status})


# ---------------------------------------------------------------------------
# 3. Save courses
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
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
        credits_val = c.get("credits", 0)
        credits, err = _parse_decimal(credits_val, f"{prefix}.credits", min_val=0)
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
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "courses_count": len(normalised),
    })


# ---------------------------------------------------------------------------
# 4. Stage sections
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
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

    sections_raw = request.data.get("sections")
    if not isinstance(sections_raw, list):
        return Response({"error": "sections must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    if len(sections_raw) == 0:
        return Response({"error": "At least one section is required"}, status=status.HTTP_400_BAD_REQUEST)

    valid_course_codes = {c["code"] for c in session.courses_config}
    errors = []
    normalised = []

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

        teacher_name = (s.get("teacher_name") or "").strip()
        grade_band = (s.get("grade_band") or "").strip()

        normalised.append({
            "course_code": course_code,
            "teacher_name": teacher_name,
            "grade_band": grade_band,
        })

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.sections_config = normalised
    session.status = SchedulingWizardSession.STATUS_SECTIONS_STAGED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "sections_count": len(normalised),
    })


# ---------------------------------------------------------------------------
# 5. Commit
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    # Idempotency guard
    if session.status == SchedulingWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **session.commit_result})

    if session.status != SchedulingWizardSession.STATUS_SECTIONS_STAGED:
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)

    courses_config = session.courses_config
    sections_config = session.sections_config

    courses_created = 0
    sections_created = 0
    courses_skipped = 0
    sections_skipped = 0

    with transaction.atomic():
        # Map course code → Course object
        course_map = {}
        for c in courses_config:
            obj, created = Course.objects.get_or_create(
                school_id=school_id,
                code=c["code"],
                defaults={
                    "name": c["name"],
                    "department": c.get("department", ""),
                    "credits": Decimal(c.get("credits", "0")),
                },
            )
            course_map[c["code"]] = obj
            if created:
                courses_created += 1
            else:
                courses_skipped += 1

        for s in sections_config:
            course_obj = course_map.get(s["course_code"])
            if not course_obj:
                continue
            _, created = Section.objects.get_or_create(
                school_id=school_id,
                course=course_obj,
                term=session.term,
                defaults={
                    "teacher_name": s.get("teacher_name", ""),
                    "grade_band": s.get("grade_band", ""),
                },
            )
            if created:
                sections_created += 1
            else:
                sections_skipped += 1

    commit_result = {
        "courses_created": courses_created,
        "courses_skipped": courses_skipped,
        "sections_created": sections_created,
        "sections_skipped": sections_skipped,
    }
    session.commit_result = commit_result
    session.status = SchedulingWizardSession.STATUS_COMMITTED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **commit_result,
    })


# ---------------------------------------------------------------------------
# 6. Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == SchedulingWizardSession.STATUS_VERIFIED:
        return Response({
            "session_id": str(session.id),
            "status": session.status,
            **session.commit_result,
        })

    if session.status != SchedulingWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    session.status = SchedulingWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **session.commit_result,
    })
