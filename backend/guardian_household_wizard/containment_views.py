"""Fail-closed guardian-household wizard endpoints.

These endpoints contain the verified identity-write defect while architecture issue
#1353 determines the canonical household, guardian, and student write model.
They validate tenant-bound student references but intentionally create no identity
records.
"""

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from core.models import Student
from households.scoping import get_request_school_id

from .models import GuardianHouseholdWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_RELATIONSHIPS = {"parent", "guardian", "grandparent", "sibling", "other"}
IDENTITY_ARCHITECTURE_ISSUE = 1353


def _get_session(session_id, school_id):
    return get_object_or_404(
        GuardianHouseholdWizardSession,
        id=session_id,
        school_id=school_id,
    )


def _validate_student_links(link_data, school_id):
    """Return a safe validation error without exposing another tenant's records."""
    if not isinstance(link_data, list) or not link_data:
        return "link_data must be a non-empty list"

    student_ids = []
    for index, link in enumerate(link_data):
        if not isinstance(link, dict):
            return f"link_data[{index}] must be an object"

        student_id = link.get("student_id")
        if not student_id:
            return f"link_data[{index}].student_id is required"

        relationship = link.get("relationship", "")
        if relationship not in VALID_RELATIONSHIPS:
            return (
                f"link_data[{index}].relationship must be one of "
                f"{sorted(VALID_RELATIONSHIPS)}"
            )

        student_ids.append(str(student_id))

    if len(student_ids) != len(set(student_ids)):
        return "link_data contains duplicate student_id values"

    try:
        matched_ids = {
            str(student_id)
            for student_id in Student.objects.filter(
                school_id=school_id,
                id__in=student_ids,
            ).values_list("id", flat=True)
        }
    except (ValidationError, TypeError, ValueError):
        return "link_data contains an invalid student_id"

    if set(student_ids) != matched_ids:
        return "One or more students were not found for the active school"

    return None


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def link_students(request, session_id):
    """Validate and stage tenant-bound student links without writing identity rows."""
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != GuardianHouseholdWizardSession.STATUS_GUARDIANS_ADDED:
        return Response(
            {
                "error": (
                    "Session must be in 'guardians_added' state "
                    f"(current: {session.status})"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    link_data = request.data.get("link_data")
    error = _validate_student_links(link_data, school_id)
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    session.link_data = link_data
    session.status = GuardianHouseholdWizardSession.STATUS_STUDENTS_LINKED
    session.save(update_fields=["link_data", "status", "updated_at"])

    return Response(
        {
            "session_id": str(session.id),
            "status": session.status,
            "link_count": len(link_data),
        }
    )


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    """Fail closed until the canonical identity write target is approved."""
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status in (
        GuardianHouseholdWizardSession.STATUS_COMMITTED,
        GuardianHouseholdWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {
                "session_id": str(session.id),
                "status": session.status,
                **(session.commit_result or {}),
            }
        )

    if session.status != GuardianHouseholdWizardSession.STATUS_STUDENTS_LINKED:
        return Response(
            {
                "error": (
                    "Session must be in 'students_linked' state "
                    f"(current: {session.status})"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response(
            {"error": "confirm is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    error = _validate_student_links(session.link_data, school_id)
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "error": (
                "Guardian-household commit is temporarily unavailable until "
                "the canonical identity write target is approved"
            ),
            "code": "identity_write_target_unresolved",
            "architecture_issue": IDENTITY_ARCHITECTURE_ISSUE,
            "session_id": str(session.id),
            "status": session.status,
        },
        status=status.HTTP_409_CONFLICT,
    )
