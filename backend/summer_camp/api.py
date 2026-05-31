from __future__ import annotations

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
from .models import (
    SummerCampEnrollment,
    SummerCampIncident,
    SummerCampProgram,
    SummerCampProgramConfig,
    SummerCampSession,
)
from .serializers import (
    SummerCampEnrollmentSerializer,
    SummerCampIncidentSerializer,
    SummerCampProgramConfigSerializer,
    SummerCampProgramSerializer,
    SummerCampSessionSerializer,
)
from .services import (
    board_summary,
    checkin_camper,
    checkout_camper,
    compute_camper_readiness,
    create_health_review,
    create_ledger_charge_summer_camp,
    create_program,
    create_session,
    enroll_camper,
    ensure_config,
    health_review_queue,
    mark_health_review_complete,
    missing_forms,
    parent_student_summary,
    record_incident,
    roster_today,
    update_program,
    update_session,
)
from .tenant import school_id_from_request


class SummerCampAttendanceActionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    student_id = serializers.UUIDField()
    note = serializers.CharField(required=False, allow_blank=True)
    pickup_contact_id = serializers.UUIDField(required=False, allow_null=True)
    pickup_verified = serializers.BooleanField(required=False)


class SummerCampEnrollmentCreateSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    student_id = serializers.UUIDField(required=False, allow_null=True)
    household_id = serializers.UUIDField(required=False, allow_null=True)
    registration_source = serializers.CharField(required=False, allow_blank=True)
    form_status = serializers.CharField(required=False, allow_blank=True)
    payment_status = serializers.CharField(required=False, allow_blank=True)
    health_status = serializers.CharField(required=False, allow_blank=True)
    pickup_status = serializers.CharField(required=False, allow_blank=True)
    payment_required_before_attendance = serializers.BooleanField(required=False)
    balance_due_cents = serializers.IntegerField(required=False)


class SummerCampIncidentCreateSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    student_id = serializers.UUIDField(required=False, allow_null=True)
    severity = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField()
    parent_notified = serializers.BooleanField(required=False)
    health_followup_required = serializers.BooleanField(required=False)


class SummerCampConfigWizardSerializer(serializers.Serializer):
    completed_steps = serializers.ListField(child=serializers.CharField(), required=False)
    is_completed = serializers.BooleanField(required=False)
    config = serializers.DictField(required=False)


class SummerCampBoardSummarySerializer(serializers.Serializer):
    as_of = serializers.CharField()
    sessions = serializers.IntegerField()
    registered_campers = serializers.IntegerField()
    waitlist_count = serializers.IntegerField()
    missing_forms = serializers.IntegerField()
    health_review_count = serializers.IntegerField()
    outstanding_balances = serializers.IntegerField()
    incidents_mtd = serializers.IntegerField()
    gross_revenue_cents = serializers.IntegerField()


class SummerCampGenericResponse(serializers.Serializer):
    detail = serializers.CharField()


VIEW_ROLES = {"summer_camp.view", "summer_camp.edit"}
EDIT_ROLES = {"summer_camp.edit"}


def _require_role(request, allowed: set[str]) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    school = getattr(request, "school", None)
    return any(user_has_permission(user, permission, school=school) for permission in allowed)


@extend_schema(methods=["GET"], responses=SummerCampProgramConfigSerializer)
@extend_schema(methods=["PUT"], request=SummerCampProgramConfigSerializer, responses=SummerCampProgramConfigSerializer)
@api_view(["GET", "PUT"])
def config_view(request):
    school_id = school_id_from_request(request, required=True)
    config = ensure_config(school_id)

    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return Response(SummerCampProgramConfigSerializer(config).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampProgramConfigSerializer(config, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save(school_id=school_id)
    return Response(serializer.data)


@extend_schema(methods=["GET"], responses=SummerCampProgramSerializer(many=True))
@extend_schema(methods=["POST"], request=SummerCampProgramSerializer, responses=SummerCampProgramSerializer)
@api_view(["GET", "POST"])
def programs_view(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        programs = SummerCampProgram.objects.filter(school_id=school_id).order_by("name")
        return Response(SummerCampProgramSerializer(programs, many=True).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampProgramSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    program = create_program(school_id, serializer.validated_data)
    return Response(SummerCampProgramSerializer(program).data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=SummerCampProgramSerializer)
@extend_schema(methods=["PUT"], request=SummerCampProgramSerializer, responses=SummerCampProgramSerializer)
@api_view(["GET", "PUT"])
def program_detail_view(request, program_id):
    school_id = school_id_from_request(request, required=True)

    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        program = SummerCampProgram.objects.get(id=program_id, school_id=school_id)
        return Response(SummerCampProgramSerializer(program).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    payload = SummerCampProgramSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    program = update_program(school_id, program_id, payload.validated_data)
    return Response(SummerCampProgramSerializer(program).data)


@extend_schema(methods=["GET"], responses=SummerCampSessionSerializer(many=True))
@extend_schema(methods=["POST"], request=SummerCampSessionSerializer, responses=SummerCampSessionSerializer)
@api_view(["GET", "POST"])
def sessions_view(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        sessions = SummerCampSession.objects.filter(school_id=school_id).order_by("start_date", "name")
        return Response(SummerCampSessionSerializer(sessions, many=True).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampSessionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    session = create_session(school_id, serializer.validated_data)
    return Response(SummerCampSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=SummerCampSessionSerializer)
@extend_schema(methods=["PUT"], request=SummerCampSessionSerializer, responses=SummerCampSessionSerializer)
@api_view(["GET", "PUT"])
def session_detail_view(request, session_id):
    school_id = school_id_from_request(request, required=True)

    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        session = SummerCampSession.objects.get(id=session_id, school_id=school_id)
        return Response(SummerCampSessionSerializer(session).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampSessionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    session = update_session(school_id, session_id, serializer.validated_data)
    return Response(SummerCampSessionSerializer(session).data)


@extend_schema(methods=["GET"], responses=SummerCampEnrollmentSerializer(many=True))
@extend_schema(methods=["POST"], request=SummerCampEnrollmentCreateSerializer, responses=SummerCampEnrollmentSerializer)
@api_view(["GET", "POST"])
def enrollments_view(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        session_id = request.query_params.get("session_id")
        query = SummerCampEnrollment.objects.filter(school_id=school_id)
        if session_id:
            query = query.filter(session_id=session_id)
        enrollments = query.order_by("-created_at")
        return Response(SummerCampEnrollmentSerializer(enrollments, many=True).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampEnrollmentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    enrollment = enroll_camper(
        school_id=school_id,
        student_id=payload.get("student_id"),
        session_id=payload["session_id"],
        payload={
            "household_id": payload.get("household_id"),
            "registration_source": payload.get("registration_source", "EXISTING"),
            "form_status": payload.get("form_status", "MISSING"),
            "payment_status": payload.get("payment_status", "DEPOSIT_DUE"),
            "health_status": payload.get("health_status", "NEEDS_REVIEW"),
            "pickup_status": payload.get("pickup_status", "MISSING"),
            "payment_required_before_attendance": payload.get("payment_required_before_attendance", True),
            "balance_due_cents": payload.get("balance_due_cents", 0),
        },
    )
    return Response(SummerCampEnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def session_roster_view(request, session_id):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = SummerCampEnrollment.objects.filter(
        school_id=school_id,
        session_id=session_id,
    ).select_related("student")

    payload = {
        "session_id": str(session_id),
        "rows": [
            {
                "enrollment_id": str(row.id),
                "student_id": str(row.student_id) if row.student_id else None,
                "student_name": (
                    f"{row.student.first_name} {row.student.last_name}" if row.student else "External Camper"
                ),
                "status": row.status,
                "readiness_status": row.readiness_status,
                "readiness_blockers": row.readiness_blockers,
                "form_status": row.form_status,
                "payment_status": row.payment_status,
                "health_status": row.health_status,
                "pickup_status": row.pickup_status,
                "waitlist_position": row.waitlist_position,
            }
            for row in rows
        ],
    }
    return Response(payload)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def roster_today_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response(roster_today(school_id))


@extend_schema(request=SummerCampAttendanceActionSerializer, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def attendance_checkin_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampAttendanceActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    attendance = checkin_camper(
        school_id=school_id,
        session_id=payload["session_id"],
        student_id=payload["student_id"],
        note=payload.get("note", ""),
    )
    return Response({"attendance_id": str(attendance.id), "checkin_time": attendance.checkin_time.isoformat()}, status=status.HTTP_201_CREATED)


@extend_schema(request=SummerCampAttendanceActionSerializer, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def attendance_checkout_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampAttendanceActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    attendance = checkout_camper(
        school_id=school_id,
        session_id=payload["session_id"],
        student_id=payload["student_id"],
        pickup_contact_id=payload.get("pickup_contact_id"),
        pickup_verified=payload.get("pickup_verified", False),
    )
    return Response(
        {
            "attendance_id": str(attendance.id),
            "checkout_time": attendance.checkout_time.isoformat() if attendance.checkout_time else None,
            "pickup_verified": attendance.pickup_verified,
        }
    )


@extend_schema(methods=["GET"], responses=SummerCampIncidentSerializer(many=True))
@extend_schema(methods=["POST"], request=SummerCampIncidentCreateSerializer, responses=SummerCampIncidentSerializer)
@api_view(["GET", "POST"])
def incidents_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        query = SummerCampIncident.objects.filter(school_id=school_id).order_by("-created_at")
        return Response(SummerCampIncidentSerializer(query, many=True).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SummerCampIncidentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    incident = record_incident(
        school_id=school_id,
        session_id=payload["session_id"],
        student_id=payload.get("student_id"),
        severity=payload.get("severity", "LOW"),
        category=payload.get("category", ""),
        description=payload["description"],
        parent_notified=payload.get("parent_notified", False),
        health_followup_required=payload.get("health_followup_required", False),
    )
    return Response(SummerCampIncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def missing_forms_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"rows": missing_forms(school_id)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def health_review_queue_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"rows": health_review_queue(school_id)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def parent_student_view(request, student_id):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"student_id": str(student_id), "rows": parent_student_summary(school_id, student_id)})


@extend_schema(responses=SummerCampBoardSummarySerializer)
@api_view(["GET"])
def board_summary_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response(board_summary(school_id))
