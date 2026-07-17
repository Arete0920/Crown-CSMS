"""Tenant-safe guardian-household wizard write endpoints.

The canonical operational identity target is core.Family/core.Guardian/core.Student.
Compatibility identity tables are intentionally not written by this controller.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from core.models import Family, Guardian, Student
from households.scoping import get_request_school_id

from .models import GuardianHouseholdWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_RELATIONSHIPS = {"parent", "guardian", "grandparent", "sibling", "other"}
GUARDIAN_RELATIONSHIP_MAP = {
    "parent": "GUARDIAN",
    "guardian": "GUARDIAN",
    "grandparent": "GRANDPARENT",
    "sibling": "OTHER",
    "other": "OTHER",
}


def _get_session(session_id, school_id, *, for_update=False):
    queryset = GuardianHouseholdWizardSession.objects
    if for_update:
        queryset = queryset.select_for_update()
    return get_object_or_404(queryset, id=session_id, school_id=school_id)


def _validate_student_links(link_data, school_id):
    """Validate links without exposing another tenant's records."""
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


def _split_name(raw_name, index):
    parts = str(raw_name or "").strip().split()
    if len(parts) < 2:
        raise ValueError(f"guardian_data[{index}].name must include first and last name")
    return parts[0], " ".join(parts[1:])


def _normalized_address(household_data):
    address = household_data.get("address") or {}
    if not isinstance(address, dict):
        raise ValueError("household_data.address must be an object")
    return {
        "address_line1": address.get("street") or address.get("address1") or "",
        "address_line2": address.get("address2") or "",
        "city": address.get("city") or "",
        "state": address.get("state") or "",
        "zip_code": address.get("zip") or address.get("postal_code") or "",
    }


def _prepare_guardians(guardian_data):
    if not isinstance(guardian_data, list) or not guardian_data:
        raise ValueError("guardian_data must be a non-empty list")

    prepared = []
    emails = set()
    for index, guardian in enumerate(guardian_data):
        if not isinstance(guardian, dict):
            raise ValueError(f"guardian_data[{index}] must be an object")
        first_name, last_name = _split_name(guardian.get("name"), index)
        email = str(guardian.get("email") or "").strip().lower()
        if not email:
            raise ValueError(f"guardian_data[{index}].email is required")
        if email in emails:
            raise ValueError("guardian_data contains duplicate email values")
        emails.add(email)

        custody_type = guardian.get("custody_type", "none")
        if custody_type not in {"primary", "joint", "secondary", "none"}:
            raise ValueError(
                f"guardian_data[{index}].custody_type must be primary, joint, secondary, or none"
            )

        prepared.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": str(guardian.get("phone") or "").strip() or None,
                "relationship": GUARDIAN_RELATIONSHIP_MAP.get(
                    guardian.get("relationship", "guardian"), "GUARDIAN"
                ),
                "custody_flag": custody_type in {"primary", "joint"},
            }
        )
    return prepared


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def link_students(request, session_id):
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
    school_id = get_request_school_id(request)

    try:
        with transaction.atomic():
            session = _get_session(session_id, school_id, for_update=True)

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

            student_ids = [link["student_id"] for link in session.link_data]
            students = list(
                Student.objects.select_for_update()
                .select_related("family")
                .filter(school_id=school_id, id__in=student_ids)
            )
            family_ids = {student.family_id for student in students}
            if len(family_ids) != 1:
                return Response(
                    {
                        "error": (
                            "Selected students must already belong to one canonical family; "
                            "the wizard will not silently merge or reassign families"
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            household_data = session.household_data or {}
            family_name = str(household_data.get("name") or "").strip()
            if not family_name:
                return Response(
                    {"error": "household_data.name is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            address_fields = _normalized_address(household_data)
            prepared_guardians = _prepare_guardians(session.guardian_data)

            family = Family.objects.select_for_update().get(
                id=next(iter(family_ids)), school_id=school_id
            )
            if (
                Family.objects.filter(school_id=school_id, family_name=family_name)
                .exclude(id=family.id)
                .exists()
            ):
                return Response(
                    {"error": "A different family already uses household_data.name"},
                    status=status.HTTP_409_CONFLICT,
                )

            guardian_emails = [guardian["email"] for guardian in prepared_guardians]
            conflicting_guardian = (
                Guardian.objects.select_for_update()
                .filter(school_id=school_id, email__in=guardian_emails)
                .exclude(family_id=family.id)
                .exists()
            )
            if conflicting_guardian:
                return Response(
                    {
                        "error": (
                            "One or more guardian emails already belong to another family; "
                            "no automatic identity merge was performed"
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            family.family_name = family_name
            for field, value in address_fields.items():
                setattr(family, field, value)
            family.save(
                update_fields=[
                    "family_name",
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "zip_code",
                    "updated_at",
                ]
            )

            guardian_ids = []
            for guardian_values in prepared_guardians:
                guardian, _created = Guardian.objects.update_or_create(
                    school_id=school_id,
                    email=guardian_values["email"],
                    defaults={"family": family, **guardian_values},
                )
                guardian_ids.append(str(guardian.id))

            result = {
                "family_id": str(family.id),
                "guardian_ids": guardian_ids,
                "student_ids": [str(student.id) for student in students],
                "guardians_created_or_updated": len(guardian_ids),
                "students_linked": len(students),
                "canonical_model": "core",
            }
            session.commit_result = result
            session.status = GuardianHouseholdWizardSession.STATUS_COMMITTED
            session.save(update_fields=["commit_result", "status", "updated_at"])

            return Response(
                {"session_id": str(session.id), "status": session.status, **result}
            )
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response(
            {"error": "Guardian-household commit violated an identity constraint"},
            status=status.HTTP_409_CONFLICT,
        )
