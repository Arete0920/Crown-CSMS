"""
guardian_household_wizard/views.py

Steps:
  POST   /sessions/                             → create_session
  POST   /sessions/<uuid>/configure/            → configure_session  (household_data)
  POST   /sessions/<uuid>/add_guardians/        → add_guardians      (guardian_data)
  POST   /sessions/<uuid>/link_students/        → link_students      (link_data)
  POST   /sessions/<uuid>/commit/               → commit_session
  GET    /sessions/<uuid>/verify/               → verify_session
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id

from .models import GuardianHouseholdWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_CUSTODY = {"primary", "joint", "none"}
VALID_RELATIONSHIPS = {"parent", "guardian", "grandparent", "sibling", "other"}


def _get_session(session_id, school_id):
    return get_object_or_404(GuardianHouseholdWizardSession, id=session_id, school__id=school_id)


# ---------------------------------------------------------------------------
# Step 1: Create session
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = GuardianHouseholdWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Step 2: Configure household
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == GuardianHouseholdWizardSession.STATUS_COMMITTED:
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

    household_data = request.data.get("household_data")
    if not isinstance(household_data, dict) or not household_data.get("name"):
        return Response({"error": "household_data.name is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.household_data = household_data
    session.status = GuardianHouseholdWizardSession.STATUS_HOUSEHOLD_CONFIGURED
    session.save()

    return Response({"session_id": str(session.id), "status": session.status})


# ---------------------------------------------------------------------------
# Step 3: Add guardians
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def add_guardians(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != GuardianHouseholdWizardSession.STATUS_HOUSEHOLD_CONFIGURED:
        return Response(
            {"error": f"Session must be in 'household_configured' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    guardian_data = request.data.get("guardian_data")
    if not isinstance(guardian_data, list) or len(guardian_data) == 0:
        return Response({"error": "guardian_data must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    for i, g in enumerate(guardian_data):
        if not g.get("name"):
            return Response({"error": f"guardian_data[{i}].name is required"}, status=status.HTTP_400_BAD_REQUEST)
        custody = g.get("custody_type", "none")
        if custody not in VALID_CUSTODY:
            return Response(
                {"error": f"guardian_data[{i}].custody_type must be one of {sorted(VALID_CUSTODY)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    session.guardian_data = guardian_data
    session.status = GuardianHouseholdWizardSession.STATUS_GUARDIANS_ADDED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "guardian_count": len(guardian_data),
    })


# ---------------------------------------------------------------------------
# Step 4: Link students
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def link_students(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != GuardianHouseholdWizardSession.STATUS_GUARDIANS_ADDED:
        return Response(
            {"error": f"Session must be in 'guardians_added' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    link_data = request.data.get("link_data")
    if not isinstance(link_data, list) or len(link_data) == 0:
        return Response({"error": "link_data must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    for i, link in enumerate(link_data):
        if not link.get("student_id"):
            return Response({"error": f"link_data[{i}].student_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        rel = link.get("relationship", "")
        if rel not in VALID_RELATIONSHIPS:
            return Response(
                {"error": f"link_data[{i}].relationship must be one of {sorted(VALID_RELATIONSHIPS)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    session.link_data = link_data
    session.status = GuardianHouseholdWizardSession.STATUS_STUDENTS_LINKED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "link_count": len(link_data),
    })


# ---------------------------------------------------------------------------
# Step 5: Commit
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == GuardianHouseholdWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})

    if session.status != GuardianHouseholdWizardSession.STATUS_STUDENTS_LINKED:
        return Response(
            {"error": f"Session must be in 'students_linked' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    from households.models import Household, Guardian, HouseholdStudent

    with transaction.atomic():
        hd = session.household_data
        household = Household.objects.create(
            school_id=school_id,
            name=hd.get("name", ""),
            address=hd.get("address", {}),
        )

        guardian_objects = []
        for g in session.guardian_data:
            guardian = Guardian.objects.create(
                school_id=school_id,
                household=household,
                name=g.get("name", ""),
                email=g.get("email", ""),
                custody_type=g.get("custody_type", "none"),
                contact_priority=g.get("contact_priority", 1),
                receives_communications=g.get("receives_communications", True),
            )
            guardian_objects.append(guardian)

        linked = 0
        for link in session.link_data:
            HouseholdStudent.objects.create(
                household=household,
                student_id=link["student_id"],
                relationship=link.get("relationship", "other"),
            )
            linked += 1

        result = {
            "household_id": str(household.id),
            "guardians_created": len(guardian_objects),
            "students_linked": linked,
        }
        session.commit_result = result
        session.status = GuardianHouseholdWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **result})


# ---------------------------------------------------------------------------
# Step 6: Verify
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        GuardianHouseholdWizardSession.STATUS_COMMITTED,
        GuardianHouseholdWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Session must be committed before verify (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.status == GuardianHouseholdWizardSession.STATUS_COMMITTED:
        session.status = GuardianHouseholdWizardSession.STATUS_VERIFIED
        session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **(session.commit_result or {}),
    })
