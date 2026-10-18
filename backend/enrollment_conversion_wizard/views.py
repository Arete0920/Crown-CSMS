from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from admissions.models import AdmissionsApplication
from admissions.services import finalize_enrollment
from households.scoping import get_request_school_id

from .models import EnrollmentConversionWizardSession
from .permissions import require_enrollment_conversion_access
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

# Direct enrollment conversion is valid only after an admissions decision has
# reached ACCEPTED. WAITLISTED must first follow the canonical WAITLISTED ->
# ACCEPTED transition.
VALID_FROM_STATUSES = {AdmissionsApplication.STATUS_ACCEPTED}


def _get_session(session_id, school_id):
    return get_object_or_404(EnrollmentConversionWizardSession, id=session_id, school__id=school_id)


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
        applications = list(
            AdmissionsApplication.objects.select_for_update()
            .select_related("sis_student")
            .filter(id__in=session.application_ids, school__id=school_id)
            .order_by("id")
        )

        expected_count = len(session.application_ids)
        if len(applications) != expected_count:
            return Response(
                {"error": "One or more selected applications are no longer available in this tenant."},
                status=status.HTTP_409_CONFLICT,
            )

        invalid = [
            app
            for app in applications
            if app.status not in {
                AdmissionsApplication.STATUS_ACCEPTED,
                AdmissionsApplication.STATUS_ENROLLED,
            }
        ]
        if invalid:
            return Response(
                {
                    "error": "Enrollment conversion requires ACCEPTED applications.",
                    "invalid_applications": [
                        {"application_id": app.id, "status": app.status} for app in invalid
                    ],
                },
                status=status.HTTP_409_CONFLICT,
            )

        converted = 0
        for app in applications:
            _app, changed = finalize_enrollment(
                app,
                actor_user=request.user,
                details={
                    "source": "enrollment_conversion_wizard",
                    "session_id": str(session.id),
                },
            )
            converted += int(changed)

        result = {"converted": converted, "selected": expected_count}
        session.commit_result = result
        session.status = EnrollmentConversionWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"status": session.status, **result})


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
        id__in=session.application_ids,
        school__id=school_id,
        academic_year__name=session.academic_year_label,
        status=AdmissionsApplication.STATUS_ENROLLED,
    ).count()

    selected_count = len(session.application_ids)
    all_enrolled = enrolled_count == selected_count
    if not all_enrolled:
        return Response(
            {
                "status": session.status,
                "enrolled_count": enrolled_count,
                "selected_count": selected_count,
                "all_enrolled": False,
                "error": "Enrollment verification failed for one or more selected applications.",
            },
            status=status.HTTP_409_CONFLICT,
        )

    session.status = EnrollmentConversionWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "status": session.status,
        "enrolled_count": enrolled_count,
        "selected_count": selected_count,
        "all_enrolled": True,
        "academic_year_label": session.academic_year_label,
        "commit_result": session.commit_result,
    })
