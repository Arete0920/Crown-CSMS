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
from admissions.views_enroll import _canonical_application_for_legacy
from applications.models import Application
from applications.views_admissions import (
    _apply_lifecycle_chain_updates,
    _latest_enrollment_state_for_application,
    _validate_lifecycle_chain_request,
)
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


class _EnrollmentReadinessChanged(Exception):
    """An enrollment cohort must roll back as a unit if canonical readiness changes."""



def _get_session(session_id, school_id):
    return get_object_or_404(EnrollmentConversionWizardSession, id=session_id, school__id=school_id)


def _get_session_locked(session_id, school_id):
    return get_object_or_404(
        EnrollmentConversionWizardSession.objects.select_for_update(),
        id=session_id,
        school_id=school_id,
    )


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

    academic_year_label = request.data.get("academic_year_label")
    if not isinstance(academic_year_label, str) or not academic_year_label.strip():
        return Response({"error": "academic_year_label is required"}, status=status.HTTP_400_BAD_REQUEST)
    academic_year_label = academic_year_label.strip()

    from_status = request.data.get("from_status", AdmissionsApplication.STATUS_ACCEPTED)
    if not isinstance(from_status, str):
        return Response({"error": "from_status must be ACCEPTED"}, status=status.HTTP_400_BAD_REQUEST)
    from_status = from_status.strip().upper()
    if from_status not in VALID_FROM_STATUSES:
        return Response(
            {"error": f"from_status must be one of: {sorted(VALID_FROM_STATUSES)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        session = _get_session_locked(session_id, school_id)
        if session.status not in (
            EnrollmentConversionWizardSession.STATUS_DRAFT,
            EnrollmentConversionWizardSession.STATUS_CONFIGURED,
        ):
            return Response(
                {"error": "Cannot reconfigure a loaded or finalized enrollment cohort."},
                status=status.HTTP_409_CONFLICT,
            )
        session.academic_year_label = academic_year_label
        session.from_status = from_status
        session.application_ids = []
        session.commit_result = None
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

    with transaction.atomic():
        session = _get_session_locked(session_id, school_id)
        if session.status not in (
            EnrollmentConversionWizardSession.STATUS_CONFIGURED,
            EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED,
        ):
            return Response(
                {"error": f"Cannot load applicants from status '{session.status}'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        app_ids = list(
            AdmissionsApplication.objects.filter(
                school_id=school_id,
                academic_year__school_id=school_id,
                academic_year__name=session.academic_year_label,
                status=session.from_status,
            ).order_by("id").values_list("id", flat=True)
        )
        session.application_ids = [str(app_id) for app_id in app_ids]
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

    if request.data.get("confirm") is not True:
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            # Serialize commits with configure/load/other commit calls. A retry must
            # return the first immutable receipt, not overwrite converted with zero.
            session = _get_session_locked(session_id, school_id)
            if session.status in (
                EnrollmentConversionWizardSession.STATUS_COMMITTED,
                EnrollmentConversionWizardSession.STATUS_VERIFIED,
            ):
                if not isinstance(session.commit_result, dict):
                    return Response(
                        {"error": "The committed conversion receipt is missing."},
                        status=status.HTTP_409_CONFLICT,
                    )
                return Response({"status": session.status, **session.commit_result})
            if session.status != EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED:
                return Response(
                    {"error": f"Cannot commit from status '{session.status}'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            expected_count = len(session.application_ids)
            if expected_count == 0:
                return Response(
                    {"error": "No accepted applications were selected for enrollment."},
                    status=status.HTTP_409_CONFLICT,
                )

            # Do not join nullable sis_student when locking PostgreSQL rows:
            # FOR UPDATE cannot target the nullable side of an outer join.
            applications = list(
                AdmissionsApplication.objects.select_for_update()
                .filter(
                    id__in=session.application_ids,
                    school_id=school_id,
                    academic_year__school_id=school_id,
                    academic_year__name=session.academic_year_label,
                    family__school_id=school_id,
                )
                .order_by("id")
            )
            if len(applications) != expected_count:
                return Response(
                    {"error": "One or more selected applications changed school or academic year."},
                    status=status.HTTP_409_CONFLICT,
                )
            if any(
                app.status not in (
                    AdmissionsApplication.STATUS_ACCEPTED,
                    AdmissionsApplication.STATUS_ENROLLED,
                )
                for app in applications
            ):
                return Response(
                    {"error": "Enrollment conversion requires ACCEPTED applications."},
                    status=status.HTTP_409_CONFLICT,
                )

            # Validate the entire selected cohort before the first enrollment
            # write, using the SAME canonical readiness gate as single enrollment.
            ready = []
            for app in applications:
                linked = _canonical_application_for_legacy(app, school_id)
                if linked is None:
                    return Response(
                        {"error": "A selected application has no linked canonical admissions record."},
                        status=status.HTTP_409_CONFLICT,
                    )
                canonical = Application.objects.select_for_update().filter(
                    pk=linked.pk, school_id=school_id
                ).first()
                if canonical is None:
                    return Response(
                        {"error": "A selected canonical application is unavailable."},
                        status=status.HTTP_409_CONFLICT,
                    )
                readiness_error = _validate_lifecycle_chain_request(
                    app=canonical,
                    state=_latest_enrollment_state_for_application(canonical),
                    requested_enrollment=True,
                    requested_classroom_ready=False,
                    requested_portal_activation=False,
                )
                if readiness_error is not None:
                    return Response(
                        {"error": "A selected application lacks canonical contract/deposit readiness."},
                        status=status.HTTP_409_CONFLICT,
                    )
                ready.append((app, canonical))

            converted = 0
            for app, canonical in ready:
                _events, lifecycle_error = _apply_lifecycle_chain_updates(
                    app=canonical,
                    actor_user=request.user,
                    note="Enrollment conversion wizard",
                    request_payload={"mark_enrollment_confirmed": True},
                )
                if lifecycle_error is not None:
                    # Returning inside atomic would commit earlier cohort writes.
                    raise _EnrollmentReadinessChanged()
                _app, changed = finalize_enrollment(
                    app,
                    actor_user=request.user,
                    details={
                        "source": "enrollment_conversion_wizard",
                        "session_id": str(session.id),
                        "canonical_application_id": str(canonical.id),
                    },
                )
                converted += int(changed)

            result = {"converted": converted, "selected": expected_count}
            session.commit_result = result
            session.status = EnrollmentConversionWizardSession.STATUS_COMMITTED
            session.save()
    except _EnrollmentReadinessChanged:
        return Response(
            {"error": "Canonical enrollment readiness changed; no cohort changes were committed."},
            status=status.HTTP_409_CONFLICT,
        )

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
    all_enrolled = selected_count > 0 and enrolled_count == selected_count
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
