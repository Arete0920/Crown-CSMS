"""Admissions enrollment action.

POST /api/admissions/enroll/
Body: {"application_id": <int>}

Requires tenant-scoped ``admissions.edit`` authority (staff/superuser remains
an explicit administrative override). A legacy admissions row may be enrolled
only when it is linked to the canonical applications lifecycle and that
canonical application has a countersigned contract plus a paid or waived
deposit.
"""

import re
from uuid import UUID

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication
from admissions.services import finalize_enrollment
from applications.models import Application
from applications.views_admissions import (
    CONTRACT_COUNTERSIGNED, DEPOSIT_PAID, DEPOSIT_WAIVED,
    _apply_lifecycle_chain_updates, _application_is_post_acceptance,
    _latest_enrollment_state_for_application, _validate_lifecycle_chain_request,
)
from applications.views_admissions_identity import (
    _upsert_verified_legacy_admissions, _verified_admissions_context,
)
from core.models import Enrollment as CoreEnrollment, School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id

_CANONICAL_APPLICATION_RE = re.compile(r"canonical_application_id=([0-9a-fA-F-]{36})")


def _require_enrollment_access(request, school):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return Response({"ok": False, "detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return None
    if user_has_permission(user, "admissions.edit", school=school):
        return None
    return Response({"ok": False, "detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)


def _canonical_application_for_legacy(app, school_id):
    # Historical notes are untrusted: one exact, normalized marker line only.
    markers = [
        line.strip()
        for line in str(getattr(app, "notes_internal", "") or "").splitlines()
        if "canonical_application_id=" in line
    ]
    if len(markers) != 1:
        return None
    match = _CANONICAL_APPLICATION_RE.fullmatch(markers[0])
    if match is None:
        return None
    try:
        canonical_id = UUID(match.group(1))
    except (TypeError, ValueError):
        return None
    if markers[0] != f"canonical_application_id={canonical_id}":
        return None
    return Application.objects.filter(id=canonical_id, school_id=school_id).first()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll_applicant(request):
    school_id = get_request_school_id(request, required=True)
    school = School.objects.get(pk=school_id)
    denied = _require_enrollment_access(request, school)
    if denied is not None:
        return denied

    application_id = request.data.get("application_id")
    if application_id is None or application_id == "":
        return Response({"ok": False, "detail": "application_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    raw_id = str(application_id)
    if (
        isinstance(application_id, bool)
        or not isinstance(application_id, (str, int))
        or re.fullmatch(r"[0-9]{1,19}", raw_id) is None
        or not 1 <= int(raw_id) <= 9223372036854775807
    ):
        return Response(
            {"ok": False, "detail": "application_id must be a positive integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    application_id = int(raw_id)

    # Resolve the canonical application first. The authoritative conversion
    # path locks canonical identity before legacy rows; preserve that order.
    candidate = AdmissionsApplication.objects.filter(
        id=application_id, school=school,
    ).first()
    if candidate is None:
        return Response({"ok": False, "detail": "Application not found."},
                        status=status.HTTP_404_NOT_FOUND)
    canonical = _canonical_application_for_legacy(candidate, school_id)
    if canonical is None:
        return Response(
            {"ok": False, "detail": "Enrollment requires a linked canonical admissions application.",
             "current_status": candidate.status},
            status=status.HTTP_409_CONFLICT,
        )

    with transaction.atomic():
        context, identity_error = _verified_admissions_context(
            school=school, application_id=canonical.id,
        )
        if identity_error is not None:
            return identity_error
        assert context is not None

        # Re-lock and revalidate all untrusted legacy linkage and stage data.
        app = AdmissionsApplication.objects.select_for_update().filter(
            id=application_id, school=school,
        ).first()
        if app is None:
            return Response({"ok": False, "detail": "Application not found."},
                            status=status.HTTP_404_NOT_FOUND)
        if app.status not in {
            AdmissionsApplication.STATUS_ACCEPTED, AdmissionsApplication.STATUS_ENROLLED,
        }:
            return Response(
                {"ok": False, "detail": "Enrollment is not permitted from the current application status.",
                 "current_status": app.status},
                status=status.HTTP_409_CONFLICT,
            )
        linked = _canonical_application_for_legacy(app, school_id)
        if linked is None or linked.id != context.application.id:
            return Response(
                {"ok": False, "detail": "Canonical admissions linkage changed during enrollment."},
                status=status.HTTP_409_CONFLICT,
            )
        if not _application_is_post_acceptance(context.application):
            return Response(
                {"ok": False, "detail": "Canonical admissions acceptance is required."},
                status=status.HTTP_409_CONFLICT,
            )

        canonical_state = _latest_enrollment_state_for_application(context.application)
        # An old ENROLLMENT_CONFIRMED event cannot waive current policy gates.
        if (
            canonical_state.get("contract_status") != CONTRACT_COUNTERSIGNED
            or canonical_state.get("deposit_status") not in {DEPOSIT_PAID, DEPOSIT_WAIVED}
        ):
            return Response(
                {"ok": False, "detail": "Canonical enrollment readiness is incomplete.",
                 "canonical_application_id": str(context.application.id),
                 "contract_status": canonical_state.get("contract_status"),
                 "deposit_status": canonical_state.get("deposit_status")},
                status=status.HTTP_409_CONFLICT,
            )
        readiness_error = _validate_lifecycle_chain_request(
            app=context.application, state=canonical_state,
            requested_enrollment=True, requested_classroom_ready=False,
            requested_portal_activation=False,
        )
        if readiness_error is not None:
            return readiness_error

        # Admissions has an explicit target year; a future-year enrollment
        # must not silently be reinterpreted as the school's current year.
        target_year = app.academic_year
        if (
            target_year.school_id != school.pk
            or app.family_id != context.family.id
            or app.student_id not in {identity.core_student.pk for identity in context.identities}
        ):
            return Response(
                {"ok": False, "detail": "Legacy student, family, or year does not match verified canonical identity.",
                 "code": "canonical_enrollment_identity_mismatch"},
                status=status.HTTP_409_CONFLICT,
            )

        # finalize_enrollment alone changes an admissions status; it does not
        # create core.Enrollment. Deny rather than reporting false SIS success.
        for identity in context.identities:
            grade = str(identity.applicant.grade_applying_for or "").strip().upper()
            enrolled = grade and CoreEnrollment.objects.select_for_update(
                of=("self",)
            ).filter(
                school=school, student=identity.core_student,
                academic_year=target_year, grade_level__school=school,
                grade_level__code=grade, status="ENROLLED",
            ).exists()
            if not enrolled:
                return Response(
                    {"ok": False,
                     "detail": "Verified canonical school-year enrollment is required.",
                     "code": "canonical_enrollment_required",
                     "applicant_id": str(identity.applicant.id)},
                    status=status.HTTP_409_CONFLICT,
                )

        _events, lifecycle_error = _apply_lifecycle_chain_updates(
            app=context.application, actor_user=request.user,
            note="Admissions pipeline enrollment action",
            request_payload={"mark_enrollment_confirmed": True},
        )
        if lifecycle_error is not None:
            transaction.set_rollback(True)
            return lifecycle_error
        app, converted = finalize_enrollment(
            app, actor_user=request.user,
            details={"source": "admissions_enroll_api",
                     "canonical_application_id": str(context.application.id)},
        )
        bridge, bridge_error = _upsert_verified_legacy_admissions(
            school=school, context=context, actor_user=request.user,
            target_status=AdmissionsApplication.STATUS_ENROLLED,
            academic_year=target_year,
        )
        if bridge_error is not None:
            transaction.set_rollback(True)
            return bridge_error

        student = app.student or app.sis_student
        student_id = str(student.id) if student else None
        student_name = str(student) if student else None

    return Response(
        {"ok": True, "already_enrolled": not converted,
         "student_id": student_id, "name": student_name,
         "canonical_application_id": str(context.application.id),
         "canonical_gate": "verified_identity_and_core_enrollment",
         "legacy_conversion_bridge": bridge,
         "message": "Enrolled successfully." if converted else "Already enrolled."},
        status=status.HTTP_200_OK,
    )
