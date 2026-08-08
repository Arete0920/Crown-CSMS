"""Admissions enrollment action.

POST /api/admissions/enroll/
Body: {"application_id": <int>}

Requires tenant-scoped ``admissions.edit`` authority (staff/superuser remains
an explicit administrative override). Uses the canonical guarded enrollment
service so status, audit, and linked SIS activation stay consistent.
"""

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication
from admissions.services import InvalidStageTransition, finalize_enrollment
from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


def _require_enrollment_access(request, school):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return Response(
            {"ok": False, "detail": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return None
    if user_has_permission(user, "admissions.edit", school=school):
        return None
    return Response(
        {"ok": False, "detail": "Permission denied."},
        status=status.HTTP_403_FORBIDDEN,
    )


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
        return Response(
            {"ok": False, "detail": "application_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        try:
            app = (
                AdmissionsApplication.objects.select_for_update()
                .select_related("sis_student")
                .get(id=application_id, school=school)
            )
        except AdmissionsApplication.DoesNotExist:
            return Response(
                {"ok": False, "detail": "Application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            app, converted = finalize_enrollment(
                app,
                actor_user=request.user,
                details={"source": "admissions_enroll_api"},
            )
        except InvalidStageTransition:
            return Response(
                {
                    "ok": False,
                    "detail": "Enrollment is not permitted from the current application status.",
                    "current_status": app.status,
                },
                status=status.HTTP_409_CONFLICT,
            )

        student_id = str(app.sis_student.id) if app.sis_student else None
        student_name = str(app.sis_student) if app.sis_student else None

    return Response(
        {
            "ok": True,
            "already_enrolled": not converted,
            "student_id": student_id,
            "name": student_name,
            "message": "Enrolled successfully." if converted else "Already enrolled.",
        },
        status=status.HTTP_200_OK,
    )
