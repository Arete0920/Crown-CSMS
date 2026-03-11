import uuid as _uuid
import logging

from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from academics.models import Enrollment, Section
from households.scoping import get_request_school_id

from .models import SectionAssignWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_ACTIONS = {"add", "remove"}
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(SectionAssignWizardSession, id=session_id, school__id=school_id)


def _parse_uuid(value, field_name):
    try:
        return _uuid.UUID(str(value)), None
    except (ValueError, AttributeError):
        return None, f"{field_name} must be a valid UUID"


# ---------------------------------------------------------------------------
# Step 1: Create session
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = SectionAssignWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Step 2: Configure (section + term)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == SectionAssignWizardSession.STATUS_COMMITTED:
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

    section_id_raw = request.data.get("section_id")
    term = str(request.data.get("term", "")).strip()

    if not section_id_raw:
        return Response({"error": "section_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    section_uuid, err = _parse_uuid(section_id_raw, "section_id")
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    # Verify section belongs to this school
    section = get_object_or_404(Section, id=section_uuid, school_id=school_id)

    if not term:
        term = section.term  # inherit from section if not provided

    session.section_id = section_uuid
    session.term = term
    session.status = SectionAssignWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "section_id": str(section_uuid),
        "term": term,
    })


# ---------------------------------------------------------------------------
# Step 3: Load student pool
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def load_students(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != SectionAssignWizardSession.STATUS_CONFIGURED:
        return Response(
            {"error": f"Session must be in 'configured' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    student_ids_raw = request.data.get("student_ids", [])
    if not isinstance(student_ids_raw, list) or len(student_ids_raw) == 0:
        return Response({"error": "student_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate and deduplicate
    seen = set()
    valid_ids = []
    errors = []
    for i, sid in enumerate(student_ids_raw):
        parsed, err = _parse_uuid(sid, f"student_ids[{i}]")
        if err:
            errors.append(err)
        elif str(parsed) not in seen:
            seen.add(str(parsed))
            valid_ids.append(str(parsed))

    if errors:
        return Response({"error": errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    session.student_pool = valid_ids
    session.status = SectionAssignWizardSession.STATUS_STUDENTS_LOADED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "student_count": len(valid_ids),
    })


# ---------------------------------------------------------------------------
# Step 4: Stage roster changes
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_roster(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != SectionAssignWizardSession.STATUS_STUDENTS_LOADED:
        return Response(
            {"error": f"Session must be in 'students_loaded' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    changes_raw = request.data.get("changes", [])
    if not isinstance(changes_raw, list) or len(changes_raw) == 0:
        return Response({"error": "changes must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    seen = {}  # student_id → last action (dedup by keeping last)
    errors = []
    for i, change in enumerate(changes_raw):
        sid_raw = change.get("student_id")
        action = change.get("action", "")

        parsed, err = _parse_uuid(sid_raw, f"changes[{i}].student_id")
        if err:
            errors.append(err)
            continue

        if action not in VALID_ACTIONS:
            errors.append(f"changes[{i}].action must be 'add' or 'remove'")
            continue

        seen[str(parsed)] = action

    if errors:
        return Response({"error": errors[0]}, status=status.HTTP_400_BAD_REQUEST)

    staged = [{"student_id": sid, "action": act} for sid, act in seen.items()]
    session.roster_changes = staged
    session.status = SectionAssignWizardSession.STATUS_ROSTER_STAGED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "changes_count": len(staged),
    })


# ---------------------------------------------------------------------------
# Step 5: Commit
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == SectionAssignWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **session.commit_result})

    if session.status != SectionAssignWizardSession.STATUS_ROSTER_STAGED:
        return Response(
            {"error": f"Session must be in 'roster_staged' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    section = get_object_or_404(Section, id=session.section_id, school_id=school_id)

    enrolled = 0
    removed = 0

    with transaction.atomic():
        for change in session.roster_changes:
            student_id = _uuid.UUID(change["student_id"])
            action = change["action"]
            if action == "add":
                try:
                    _, created = Enrollment.objects.get_or_create(
                        section=section,
                        student_id=student_id,
                        defaults={"school_id": school_id},
                    )
                    if created:
                        enrolled += 1
                except IntegrityError as exc:
                    logger.warning(
                        "Skipping enrollment add for section %s student %s: %s",
                        section.id,
                        student_id,
                        exc,
                    )
            elif action == "remove":
                deleted, _ = Enrollment.objects.filter(
                    section=section, student_id=student_id
                ).delete()
                if deleted:
                    removed += 1

        result = {"enrolled": enrolled, "removed": removed}
        session.commit_result = result
        session.status = SectionAssignWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **result})


# ---------------------------------------------------------------------------
# Step 6: Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        SectionAssignWizardSession.STATUS_COMMITTED,
        SectionAssignWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Session must be committed before verify (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Count current enrollments for the section
    enrollment_count = Enrollment.objects.filter(
        section_id=session.section_id, school_id=school_id
    ).count()

    if session.status == SectionAssignWizardSession.STATUS_COMMITTED:
        session.status = SectionAssignWizardSession.STATUS_VERIFIED
        session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "enrollment_count": enrollment_count,
        **(session.commit_result or {}),
    })
