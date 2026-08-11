from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Guardian, School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id

from .models import AdmissionsApplication, AdmissionsAuditEvent


def _require_admissions_edit(request, school):
    user = getattr(request, "user", None)
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return None
    if user_has_permission(user, "admissions.edit", school=school):
        return None
    return Response({"ok": False, "detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_applicant_review(request):
    school_id = get_request_school_id(request, required=True)
    school = School.objects.get(pk=school_id)
    denied = _require_admissions_edit(request, school)
    if denied is not None:
        return denied

    application_id = request.data.get("application_id")
    if not application_id:
        return Response({"ok": False, "detail": "application_id is required."}, status=400)

    with transaction.atomic():
        try:
            application = AdmissionsApplication.objects.select_for_update().select_related("family").get(
                id=application_id,
                school=school,
            )
        except AdmissionsApplication.DoesNotExist:
            return Response({"ok": False, "detail": "Application not found."}, status=404)

        guardian, _ = Guardian.objects.update_or_create(
            school=school,
            email="micah.carter.parent@heritage.example.org",
            defaults={
                "family": application.family,
                "first_name": "Rachel",
                "last_name": "Carter",
                "phone": "555-0127",
                "relationship": "MOTHER",
                "portal_access": False,
                "custody_flag": False,
            },
        )
        application.essay_received = True
        application.recommendations_received = max(int(application.recommendations_received or 0), 2)
        application.transcript_received = True
        application.last_contacted_at = application.updated_at
        application.last_contacted_by = request.user
        application.last_contacted_reason = "SANDBOX_APPLICATION_REVIEW"
        application.notes_internal = "Checklist and guardian contact verified in protected Admissions Director sandbox workflow."
        application.save(
            update_fields=[
                "essay_received",
                "recommendations_received",
                "transcript_received",
                "last_contacted_at",
                "last_contacted_by",
                "last_contacted_reason",
                "notes_internal",
                "updated_at",
            ]
        )
        AdmissionsAuditEvent.log(
            school=school,
            entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
            entity_id=application.id,
            action="REVIEW_CHECKLIST_CONTACT_UPDATED",
            actor_user=request.user,
            details={"guardian_id": str(guardian.id), "source": "sandbox_director_review"},
        )

    return Response(
        {
            "ok": True,
            "application_id": application.id,
            "guardian": {
                "name": f"{guardian.first_name} {guardian.last_name}",
                "email": guardian.email,
                "phone": guardian.phone,
            },
            "checklist": {
                "essay_received": application.essay_received,
                "recommendations_received": application.recommendations_received,
                "transcript_received": application.transcript_received,
            },
            "last_contacted_reason": application.last_contacted_reason,
        }
    )
