from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from admissions.models import AdmissionsApplication
from admissions.services import finalize_enrollment
from applications.views_admissions import (
    _apply_lifecycle_chain_updates,
    _latest_enrollment_state_for_application,
    _validate_lifecycle_chain_request,
)
from households.scoping import get_request_school_id

from .identity import BulkEnrollmentProofError, verified_cohort
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
            session = _get_session_locked(session_id, school_id)
            if session.status in (
                EnrollmentConversionWizardSession.STATUS_COMMITTED,
                EnrollmentConversionWizardSession.STATUS_VERIFIED,
            ):
                if not isinstance(session.commit_result, dict):
                    raise BulkEnrollmentProofError("The earlier conversion receipt is missing.")
                members = verified_cohort(session, school_id, enrolled_only=True)
                if len(members) != session.commit_result.get("selected"):
                    raise BulkEnrollmentProofError("Stored receipt differs from verified SIS cohort.")
                return Response({"status": session.status, **session.commit_result})
            if session.status != EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED:
                return Response(
                    {"error": f"Cannot commit from status '{session.status}'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # All canonical applications, applicant identities and SIS records
            # must exist before this routine changes any legacy enrollment.
            members = verified_cohort(session, school_id)
            converted = 0
            confirmed = set()
            for member in members:
                if member.canonical.pk not in confirmed:
                    _events, error = _apply_lifecycle_chain_updates(
                        app=member.canonical,
                        actor_user=request.user,
                        note="Verified SIS enrollment conversion wizard",
                        request_payload={"mark_enrollment_confirmed": True},
                    )
                    if error is not None:
                        raise _EnrollmentReadinessChanged()
                    confirmed.add(member.canonical.pk)
                _app, changed = finalize_enrollment(
                    member.legacy,
                    actor_user=request.user,
                    details={
                        "source": "enrollment_conversion_wizard",
                        "session_id": str(session.pk),
                        "canonical_application_id": str(member.canonical.pk),
                    },
                )
                converted += int(changed)

            verified_cohort(session, school_id, enrolled_only=True)
            result = {"converted": converted, "selected": len(members)}
            session.commit_result = result
            session.status = EnrollmentConversionWizardSession.STATUS_COMMITTED
            session.save()
    except (BulkEnrollmentProofError, _EnrollmentReadinessChanged, IntegrityError) as exc:
        detail = str(exc) if isinstance(exc, BulkEnrollmentProofError) else "Enrollment readiness changed; no cohort changes were committed."
        return Response({"error": detail}, status=status.HTTP_409_CONFLICT)
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
    try:
        with transaction.atomic():
            session = _get_session_locked(session_id, school_id)
            if session.status not in (
                EnrollmentConversionWizardSession.STATUS_COMMITTED,
                EnrollmentConversionWizardSession.STATUS_VERIFIED,
            ):
                return Response(
                    {"error": f"Cannot verify from status '{session.status}'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            members = verified_cohort(session, school_id, enrolled_only=True)
            if (
                not isinstance(session.commit_result, dict)
                or len(members) != session.commit_result.get("selected")
            ):
                raise BulkEnrollmentProofError("Commit receipt or canonical enrollment proof is incomplete.")
            session.status = EnrollmentConversionWizardSession.STATUS_VERIFIED
            session.save(update_fields=["status", "updated_at"])
            result = {
                "status": session.status,
                "enrolled_count": len(members),
                "selected_count": len(members),
                "all_enrolled": True,
                "academic_year_label": session.academic_year_label,
                "commit_result": session.commit_result,
            }
    except (BulkEnrollmentProofError, IntegrityError) as exc:
        detail = str(exc) if isinstance(exc, BulkEnrollmentProofError) else "Verified SIS enrollment proof failed."
        return Response(
            {"all_enrolled": False, "error": detail},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(result)
