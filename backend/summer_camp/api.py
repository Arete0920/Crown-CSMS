from __future__ import annotations

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
from households.models import Guardian
from .models import (
    SummerCampClub,
    SummerCampClubOffering,
    SummerCampClubSelection,
    SummerCampEnrollment,
    SummerCampIncident,
    SummerCampProgram,
    SummerCampProgramConfig,
    SummerCampSession,
)
from .serializers import (
    SummerCampClubCreateSerializer,
    SummerCampClubOfferingCreateSerializer,
    SummerCampClubOfferingSerializer,
    SummerCampClubSelectionCreateSerializer,
    SummerCampClubSelectionSerializer,
    SummerCampClubSerializer,
    SummerCampEnrollmentSerializer,
    SummerCampIncidentSerializer,
    SummerCampProgramConfigSerializer,
    SummerCampProgramSerializer,
    SummerCampSessionSerializer,
)
from .services import (
    board_summary,
    cancel_club_selection,
    checkin_camper,
    checkout_camper,
    create_club,
    create_club_offering,
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
    select_club,
    update_program,
    update_session,
)
from .tenant import school_id_from_request


class SummerCampAttendanceActionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    student_id = serializers.UUIDField()
    note = serializers.CharField(required=False, allow_blank=True)
    pickup_contact_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    pickup_verified = serializers.BooleanField(required=False)


class SummerCampEnrollmentCreateSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    student_id = serializers.UUIDField(required=False, allow_null=True)
    household_id = serializers.UUIDField(required=False, allow_null=True)
    registration_source = serializers.CharField(required=False, allow_blank=True)
    def validate(self, attrs):
        # Client-controlled clearance would allow a registration to claim that
        # forms, health review and payment were already approved.
        forbidden = {
            "form_status", "payment_status", "health_status", "pickup_status",
            "payment_required_before_attendance", "balance_due_cents",
            "readiness_status", "readiness_blockers", "status",
        }
        if forbidden.intersection(self.initial_data):
            raise serializers.ValidationError(
                {"detail": "Camp clearance and payment status cannot be set during registration."}
            )
        return attrs


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
    """Only explicit, active, school-scoped camp grants authorize API access."""
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", True):
        return False

    school = getattr(request, "school", None)
    if school is None:
        return False
    return any(user_has_permission(user, permission, school=school) for permission in allowed)


@extend_schema(methods=["GET"], responses=SummerCampProgramConfigSerializer)
@extend_schema(methods=["PUT"], request=SummerCampProgramConfigSerializer, responses=SummerCampProgramConfigSerializer)
@api_view(["GET", "PUT"])
def config_view(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        config = ensure_config(school_id)
        return Response(SummerCampProgramConfigSerializer(config).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    config = ensure_config(school_id)
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


@extend_schema(methods=["GET"], responses=SummerCampClubSerializer(many=True))
@extend_schema(methods=["POST"], request=SummerCampClubCreateSerializer, responses=SummerCampClubSerializer)
@api_view(["GET", "POST"])
def clubs_view(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        clubs = SummerCampClub.objects.filter(school_id=school_id).order_by("name", "pk")
        return Response(SummerCampClubSerializer(clubs, many=True).data)

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    serializer = SummerCampClubCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        club = create_club(school_id, serializer.validated_data)
    except (ValueError, Exception) as exc:
        from django.core.exceptions import ValidationError as DjangoValidationError
        if not isinstance(exc, DjangoValidationError):
            raise
        return Response(
            {"detail": "Club catalog item is invalid or already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(SummerCampClubSerializer(club).data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=SummerCampClubOfferingSerializer(many=True))
@extend_schema(
    methods=["POST"],
    request=SummerCampClubOfferingCreateSerializer,
    responses=SummerCampClubOfferingSerializer,
)
@api_view(["GET", "POST"])
def club_offerings_view(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        query = SummerCampClubOffering.objects.filter(school_id=school_id).select_related("club")
        session_id = request.query_params.get("session_id")
        if session_id:
            query = query.filter(session_id=session_id)
        return Response(
            SummerCampClubOfferingSerializer(query.order_by("session_id", "start_time", "pk"), many=True).data
        )

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    serializer = SummerCampClubOfferingCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        offering = create_club_offering(school_id, serializer.validated_data)
    except (ValueError, Exception) as exc:
        from django.core.exceptions import ValidationError as DjangoValidationError
        if not isinstance(exc, (ValueError, DjangoValidationError)):
            raise
        return Response(
            {"detail": "Club offering is invalid for this school or session."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(
        SummerCampClubOfferingSerializer(offering).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(methods=["GET"], responses=SummerCampClubSelectionSerializer(many=True))
@extend_schema(
    methods=["POST"],
    request=SummerCampClubSelectionCreateSerializer,
    responses=SummerCampClubSelectionSerializer,
)
@api_view(["GET", "POST"])
def club_selections_view(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _require_role(request, VIEW_ROLES):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        query = SummerCampClubSelection.objects.filter(school_id=school_id).select_related(
            "offering", "offering__club", "enrollment"
        )
        enrollment_id = request.query_params.get("enrollment_id")
        offering_id = request.query_params.get("offering_id")
        if enrollment_id:
            query = query.filter(enrollment_id=enrollment_id)
        if offering_id:
            query = query.filter(offering_id=offering_id)
        return Response(
            SummerCampClubSelectionSerializer(query.order_by("-created_at", "pk"), many=True).data
        )

    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    serializer = SummerCampClubSelectionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        selection = select_club(
            school_id,
            serializer.validated_data["enrollment_id"],
            serializer.validated_data["offering_id"],
        )
    except ValueError:
        return Response(
            {"detail": "Club selection denied: registration, schedule, or capacity is invalid."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(
        SummerCampClubSelectionSerializer(selection).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def club_selection_cancel_view(request, selection_id):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, EDIT_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    try:
        cancelled, promoted = cancel_club_selection(school_id, selection_id)
    except ValueError:
        return Response(
            {"detail": "Club selection is unavailable or already cancelled."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response({
        "selection_id": cancelled.id,
        "status": cancelled.status,
        "promoted_selection_id": promoted.id if promoted else None,
    })


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

    try:
        enrollment = enroll_camper(
            school_id=school_id,
            student_id=payload.get("student_id"),
            session_id=payload["session_id"],
            payload={
                "household_id": payload.get("household_id"),
                "registration_source": payload.get("registration_source", "EXISTING"),
                # Intake only forwards registration identity and source.
                # Clearance/fees are derived and reviewed by trusted services.
            },
        )
    except ValueError:
        return Response(
            {"detail": "Camp registration denied: camper, session or capacity is invalid."},
            status=status.HTTP_400_BAD_REQUEST,
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
    try:
        attendance = checkin_camper(
            school_id=school_id,
            session_id=payload["session_id"],
            student_id=payload["student_id"],
            note=payload.get("note", ""),
        )
    except ValueError:
        return Response(
            {"detail": "Camp check-in denied: session, registration, or clearance is invalid."},
            status=status.HTTP_400_BAD_REQUEST,
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
    try:
        attendance = checkout_camper(
            school_id=school_id,
            session_id=payload["session_id"],
            student_id=payload["student_id"],
            pickup_contact_id=payload.get("pickup_contact_id"),
            pickup_verified=payload.get("pickup_verified", False),
            verified_by=request.user,
        )
    except ValueError:
        # Do not expose whether a pupil, enrollment or contact exists.
        return Response(
            {"detail": "Checkout requires a valid check-in and verified authorized pickup."},
            status=status.HTTP_400_BAD_REQUEST,
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
    user = getattr(request, "user", None)
    owns_student = bool(
        user and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and Guardian.objects.filter(
            account=user, school_id=school_id,
            household__students__id=student_id,
            household__students__school_id=school_id,
            household__students__is_active=True,
        ).exists()
    )
    if not owns_student and not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"student_id": str(student_id), "rows": parent_student_summary(school_id, student_id)})


@extend_schema(responses=SummerCampBoardSummarySerializer)
@api_view(["GET"])
def board_summary_view(request):
    school_id = school_id_from_request(request, required=True)
    if not _require_role(request, VIEW_ROLES):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return Response(board_summary(school_id))
