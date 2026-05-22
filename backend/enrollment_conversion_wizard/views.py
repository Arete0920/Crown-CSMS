from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from admissions.models import AdmissionsApplication
from households.scoping import get_request_school_id

from .models import EnrollmentConversionWizardSession
from .permissions import require_enrollment_conversion_access
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_FROM_STATUSES = {
    AdmissionsApplication.STATUS_ACCEPTED,
    AdmissionsApplication.STATUS_WAITLISTED,
}


def _get_session(session_id, school_id):
    return get_object_or_404(EnrollmentConversionWizardSession, id=session_id, school__id=school_id)


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)

    denied = require_enrollment_conversion_access(request, school)
    if denied is not None:
        return denied

    session = EnrollmentConversionWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({"session_id": str(session.id), "status": session.status}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# 2. Configure
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    denied = require_enrollment_conversion_access(request, session.school)
    if denied is not None:
        return denied

    academic_year_label = (request.data.get("academic_year_label") or "").strip()
    if not academic_year_label:
        return Response({"error": "academic_year_label is required"}, status=status.HTTP_400_BAD_REQUEST)

    from_status = (request.data.get("from_status") or "ACCEPTED").strip().upper()
    if from_status not in VALID_FROM_STATUSES:
        return Response(
            {"error": f"from_status must be one of: {sorted(VALID_FROM_STATUSES)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.academic_year_label = academic_year_label
    session.from_status = from_status
    session.status = EnrollmentConversionWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "academic_year_label": academic_year_label,
        "from_status": from_status,
    })


# ---------------------------------------------------------------------------
# 3. Load applicants
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def load_applicants(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    denied = require_enrollment_conversion_access(request, session.school)
    if denied is not None:
        return denied

    if session.status not in (
        EnrollmentConversionWizardSession.STATUS_CONFIGURED,
        EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED,
    ):
        return Response(
            {"error": f"Cannot load applicants from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = AdmissionsApplication.objects.filter(
        school__id=school_id,
        academic_year__name=session.academic_year_label,
        status=session.from_status,
    )
    app_ids = [str(a.id) for a in qs]

    session.application_ids = app_ids
    session.status = EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "applicant_count": len(app_ids),
    })


# ---------------------------------------------------------------------------
# 4. Commit — bulk update status → ENROLLED
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    denied = require_enrollment_conversion_access(request, session.school)
    if denied is not None:
        return denied

    if session.status not in (
        EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED,
        EnrollmentConversionWizardSession.STATUS_COMMITTED,
    ):
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        updated = AdmissionsApplication.objects.filter(
            id__in=session.application_ids,
            school__id=school_id,
        ).update(status=AdmissionsApplication.STATUS_ENROLLED)

        result = {"converted": updated}
        session.commit_result = result
        session.status = EnrollmentConversionWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"status": session.status, **result})


# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    denied = require_enrollment_conversion_access(request, session.school)
    if denied is not None:
        return denied

    if session.status not in (
        EnrollmentConversionWizardSession.STATUS_COMMITTED,
        EnrollmentConversionWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    enrolled_count = AdmissionsApplication.objects.filter(
        school__id=school_id,
        academic_year__name=session.academic_year_label,
        status=AdmissionsApplication.STATUS_ENROLLED,
    ).count()

    session.status = EnrollmentConversionWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "status": session.status,
        "enrolled_count": enrolled_count,
        "academic_year_label": session.academic_year_label,
        "commit_result": session.commit_result,
    })
