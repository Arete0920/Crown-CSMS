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

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication
from admissions.services import finalize_enrollment
from applications.models import Application
from applications.views_admissions import (
    _apply_lifecycle_chain_updates,
    _latest_enrollment_state_for_application,
    _upsert_legacy_admissions_applications,
    _validate_lifecycle_chain_request,
)
from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id

_CANONICAL_APPLICATION_RE = re.compile(r"(?:^|\s)canonical_application_id=([0-9a-fA-F-]{36})(?:\s|$)")


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
    match = _CANONICAL_APPLICATION_RE.search(str(getattr(app, "notes_internal", "") or ""))
    if match is None:
        return None
    return Application.objects.filter(id=match.group(1), school_id=school_id).first()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll_applicant(request):
    school_id = get_request_school_id(request, required=True)
    school = School.objects.get(pk=school_id)
    denied = _require_enrollment_access(request, school)
    if denied is not None:
        return denied

    application_id = request.data.get("application_id")
    if not application_id:
        return Response({"ok": False, "detail": "application_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        try:
            app = AdmissionsApplication.objects.select_for_update().get(id=application_id, school=school)
        except AdmissionsApplication.DoesNotExist:
            return Response({"ok": False, "detail": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        if app.status not in {AdmissionsApplication.STATUS_ACCEPTED, AdmissionsApplication.STATUS_ENROLLED}:
            return Response({"ok": False, "detail": "Enrollment is not permitted from the current application status.", "current_status": app.status}, status=status.HTTP_409_CONFLICT)

        canonical = _canonical_application_for_legacy(app, school_id)
        if canonical is None:
            return Response({"ok": False, "detail": "Enrollment requires a linked canonical admissions application.", "current_status": app.status}, status=status.HTTP_409_CONFLICT)

        canonical_state = _latest_enrollment_state_for_application(canonical)
        readiness_error = _validate_lifecycle_chain_request(app=canonical, state=canonical_state, requested_enrollment=True, requested_classroom_ready=False, requested_portal_activation=False)
        if readiness_error is not None:
            payload = dict(getattr(readiness_error, "data", {}) or {})
            return Response({"ok": False, "detail": payload.get("detail") or "Canonical enrollment readiness is incomplete.", "canonical_application_id": str(canonical.id), "contract_status": payload.get("contract_status", canonical_state.get("contract_status")), "deposit_status": payload.get("deposit_status", canonical_state.get("deposit_status"))}, status=status.HTTP_409_CONFLICT)

        _events, lifecycle_error = _apply_lifecycle_chain_updates(app=canonical, actor_user=request.user, note="Admissions pipeline enrollment action", request_payload={"mark_enrollment_confirmed": True})
        if lifecycle_error is not None:
            return lifecycle_error

        app, converted = finalize_enrollment(app, actor_user=request.user, details={"source": "admissions_enroll_api", "canonical_application_id": str(canonical.id)})
        _upsert_legacy_admissions_applications(app=canonical, actor_user=request.user, target_status=AdmissionsApplication.STATUS_ENROLLED)
        student = app.student or app.sis_student
        student_id = str(student.id) if student else None
        student_name = str(student) if student else None

    return Response({"ok": True, "already_enrolled": not converted, "student_id": student_id, "name": student_name, "canonical_application_id": str(canonical.id), "canonical_gate": "contract_countersigned_and_deposit_paid_or_waived", "message": "Enrolled successfully." if converted else "Already enrolled."}, status=status.HTTP_200_OK)
