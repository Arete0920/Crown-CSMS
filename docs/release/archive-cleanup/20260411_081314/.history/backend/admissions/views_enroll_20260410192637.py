"""
Admissions enrollment action.

POST /api/admissions/enroll/
Body: {"application_id": <int>}

Staff-only. Moves an AdmissionsApplication from ACCEPTED -> ENROLLED
and activates the linked sis_student record (if present).

Returns:
  - 200 OK (already enrolled):
      {
          "ok": true,
          "already_enrolled": true,
          "student_id": <str | null>,
          "name": <str | null>,
          "message": "Already enrolled."
      }
  - 200 OK (enrolled successfully):
      {
          "ok": true,
          "already_enrolled": false,
          "student_id": <str | null>,
          "name": <str | null>,
          "message": "Enrolled successfully."
      }
  - 400/401/403/404 error responses:
      {
          "ok": false,
          "detail": <str>
      }
  - 409 Conflict (invalid stage transition):
      {
          "ok": false,
          "detail": <str>,
          "current_status": <str>
      }
"""

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication
from admissions.services import InvalidStageTransition, move_stage
from households.scoping import get_request_school_id


class AdmissionsEnrollRequestSerializer(serializers.Serializer):
    application_id = serializers.CharField()


class AdmissionsEnrollResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    already_enrolled = serializers.BooleanField()
    student_id = serializers.CharField(allow_null=True, required=False)
    name = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()


class AdmissionsEnrollErrorSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    detail = serializers.CharField()
    current_status = serializers.CharField(required=False)


def _require_staff(request):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return Response(
            {"ok": False, "detail": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
        return Response(
            {"ok": False, "detail": "Staff access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


@extend_schema(
    tags=["Admissions"],
    request=AdmissionsEnrollRequestSerializer,
    responses={
        200: AdmissionsEnrollResponseSerializer,
        400: AdmissionsEnrollErrorSerializer,
        401: AdmissionsEnrollErrorSerializer,
        403: AdmissionsEnrollErrorSerializer,
        404: AdmissionsEnrollErrorSerializer,
        409: AdmissionsEnrollErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll_applicant(request):
    school_id = get_request_school_id(request, required=True)  # 400 if missing, 404 if wrong tenant

    denied = _require_staff(request)
    if denied is not None:
        return denied

    application_id = request.data.get("application_id")
    if not application_id:
        return Response(
            {"ok": False, "detail": "application_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        app = AdmissionsApplication.objects.select_related("sis_student").get(
            id=application_id, school_id=school_id
        )
    except AdmissionsApplication.DoesNotExist:
        return Response(
            {"ok": False, "detail": "Application not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if app.status == AdmissionsApplication.STATUS_ENROLLED:
        student_id = str(app.sis_student.id) if app.sis_student else None
        student_name = str(app.sis_student) if app.sis_student else None
        return Response(
            {
                "ok": True,
                "already_enrolled": True,
                "student_id": student_id,
                "name": student_name,
                "message": "Already enrolled.",
            }
        )

    with transaction.atomic():
        try:
            move_stage(app, AdmissionsApplication.STATUS_ENROLLED, actor_user=request.user)
        except InvalidStageTransition:
            return Response(
                {
                    "ok": False,
                    "detail": "Enrollment is not permitted from the current application status.",
                    "current_status": app.status,
                },
                status=status.HTTP_409_CONFLICT,
            )

        student_id = None
        student_name = None

        if app.sis_student:
            app.sis_student.active = True
            app.sis_student.save(update_fields=["active"])
            student_id = str(app.sis_student.id)
            student_name = str(app.sis_student)

    return Response(
        {
            "ok": True,
            "already_enrolled": False,
            "student_id": student_id,
            "name": student_name,
            "message": "Enrolled successfully.",
        },
        status=status.HTTP_200_OK,
    )
