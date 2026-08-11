from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication, AdmissionsDecision
from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


def _authorized(request, school: School) -> bool:
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    return user_has_permission(user, "admissions.edit", school=school)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def decide_applicant(request):
    school_id = get_request_school_id(request, required=True)
    school = School.objects.get(pk=school_id)
    if not _authorized(request, school):
        return Response({"ok": False, "detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    application_id = request.data.get("application_id")
    decision_value = str(request.data.get("decision") or "").strip().upper()
    allowed = {
        "ACCEPTED": AdmissionsDecision.DECISION_ACCEPTED,
        "WAITLISTED": AdmissionsDecision.DECISION_WAITLISTED,
        "DENIED": AdmissionsDecision.DECISION_DENIED,
    }
    if not application_id:
        return Response({"ok": False, "detail": "application_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    if decision_value not in allowed:
        return Response({"ok": False, "detail": "decision must be ACCEPTED, WAITLISTED, or DENIED."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        try:
            application = AdmissionsApplication.objects.select_for_update().get(
                id=application_id,
                school=school,
            )
        except AdmissionsApplication.DoesNotExist:
            return Response({"ok": False, "detail": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        if application.status == AdmissionsApplication.STATUS_ENROLLED:
            return Response(
                {"ok": False, "detail": "An enrolled application cannot be re-decided."},
                status=status.HTTP_409_CONFLICT,
            )

        decision, _ = AdmissionsDecision.objects.update_or_create(
            school=school,
            academic_year=application.academic_year,
            application=application,
            defaults={
                "decision_status": allowed[decision_value],
                "decided_by": request.user,
            },
        )
        decision.mark_decision_made(actor_user=request.user)
        application.refresh_from_db()

    return Response(
        {
            "ok": True,
            "application_id": application.id,
            "status": application.status,
            "decision": decision.decision_status,
            "message": f"Decision recorded: {decision.decision_status}.",
        },
        status=status.HTTP_200_OK,
    )
