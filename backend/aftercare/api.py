from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
from households.models import Guardian, Student

from .integrations import AftercareIntegrationError
from .models import AftercareAttendance, AftercareEnrollment, AftercareIncident, AftercarePickupContact
from .serializers import (
    AftercareAttendanceSerializer,
    AftercareEnrollmentSerializer,
    AftercareIncidentSerializer,
    AftercarePickupContactSerializer,
    AftercareProgramConfigSerializer,
)
from .services import checkin_student, checkout_student, ensure_config, handoff_student_to_school, record_incident
from .tenant import school_id_from_request


class RosterTodayRowSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    care_session = serializers.ChoiceField(choices=["AM", "PM"])
    enrollment = AftercareEnrollmentSerializer()
    attendance = AftercareAttendanceSerializer(allow_null=True)


class RosterTodayResponseSerializer(serializers.Serializer):
    date = serializers.CharField()
    dow = serializers.CharField()
    rows = RosterTodayRowSerializer(many=True)


class ParentViewResponseSerializer(serializers.Serializer):
    enrollment = AftercareEnrollmentSerializer(allow_null=True)
    attendance = AftercareAttendanceSerializer(many=True)


class BoardSummaryResponseSerializer(serializers.Serializer):
    as_of = serializers.CharField()
    active_enrollment = serializers.IntegerField()
    care_session = serializers.CharField()
    sessions_mtd = serializers.IntegerField()
    late_pickups_mtd = serializers.IntegerField()
    incidents_mtd = serializers.IntegerField()
    unattributed_incidents_mtd = serializers.IntegerField()
    late_fee_assessed_mtd = serializers.FloatField()
    # Legacy response key; this figure is an assessment, not cash receipts.
    late_fee_revenue_mtd = serializers.FloatField()


class AftercareCheckinRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    care_session = serializers.ChoiceField(choices=["AM", "PM"], default="PM")
    note = serializers.CharField(required=False, allow_blank=True)


class AftercareCheckoutRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    care_session = serializers.ChoiceField(choices=["PM"], default="PM")
    pickup_contact_id = serializers.IntegerField(min_value=1)
    # Legacy clients may send a freeform label, but the service never trusts it.
    pickup_name_freeform = serializers.CharField(required=False, allow_blank=True)
    pickup_verified = serializers.BooleanField()


class AftercareIncidentCreateRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    severity = serializers.ChoiceField(choices=["MINOR", "MODERATE", "MAJOR"], default="MINOR")
    description = serializers.CharField(required=False, allow_blank=True)
    attendance_id = serializers.IntegerField(required=False, allow_null=True)
    parent_notified = serializers.BooleanField(required=False)


class AftercareStudentRequiredSerializer(serializers.Serializer):
    detail = serializers.CharField()


def _has_permission(request, code: str) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user_has_permission(user, code, school=getattr(request, "school", None))


def _guardian_can_view_student(request, *, school_id, student_id) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return Guardian.objects.filter(
        account=user,
        school_id=school_id,
        household__students__id=student_id,
        household__students__school_id=school_id,
        household__students__is_active=True,
    ).exists()


def _canonical_student_exists(*, school_id, student_id) -> bool:
    return Student.objects.filter(pk=student_id, school_id=school_id, is_active=True).exists()


def _forbidden():
    return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


def _bad_request(exc):
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(methods=["GET"], responses=AftercareProgramConfigSerializer)
@extend_schema(methods=["PUT"], request=AftercareProgramConfigSerializer, responses=AftercareProgramConfigSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "PUT"])
def program_config(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _has_permission(request, "extended_care.view"):
            return _forbidden()
        cfg = ensure_config(school_id)
        return Response(AftercareProgramConfigSerializer(cfg).data)

    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    cfg = ensure_config(school_id)
    ser = AftercareProgramConfigSerializer(cfg, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save()
    return Response(ser.data)


@extend_schema(methods=["GET"], responses=AftercareEnrollmentSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercareEnrollmentSerializer, responses=AftercareEnrollmentSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
def enrollments(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _has_permission(request, "extended_care.view"):
            return _forbidden()
        qs = AftercareEnrollment.objects.filter(school_fk_id=school_id).order_by("-created_at")[:500]
        return Response(AftercareEnrollmentSerializer(qs, many=True).data)

    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercareEnrollmentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    student_id = ser.validated_data["student_fk_id"]
    with transaction.atomic():
        # Serialize same-child enrollment creation to prevent duplicate schedules
        # from triggering duplicate care attendance or recurring charges.
        student = Student.objects.select_for_update().filter(
            pk=student_id, school_id=school_id, is_active=True,
        ).first()
        if student is None:
            return _bad_request("Student is not active in this school.")

        new_start = ser.validated_data["start_date"]
        new_end = ser.validated_data.get("end_date")
        session = ser.validated_data.get("care_session", "PM")
        existing = AftercareEnrollment.objects.filter(
            school_fk_id=school_id, student_fk=student,
            care_session=session, is_active=True,
        )
        for row in existing:
            date_overlap = (
                (new_end is None or row.start_date <= new_end)
                and (row.end_date is None or row.end_date >= new_start)
            )
            if date_overlap:
                return _bad_request("Overlapping active enrollment for this care session.")
        enrollment = ser.save(school_fk_id=school_id)
    return Response(AftercareEnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=AftercarePickupContactSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercarePickupContactSerializer, responses=AftercarePickupContactSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
def pickup_contacts(request, student_id):
    school_id = school_id_from_request(request, required=True)
    if not _canonical_student_exists(school_id=school_id, student_id=student_id):
        return _bad_request("Student is not active in this school.")

    if request.method == "GET":
        if not (
            _has_permission(request, "extended_care.view")
            or _guardian_can_view_student(request, school_id=school_id, student_id=student_id)
        ):
            return _forbidden()
        qs = AftercarePickupContact.objects.filter(
            school_fk_id=school_id, student_fk_id=student_id, is_active=True
        )
        return Response(AftercarePickupContactSerializer(qs, many=True).data)

    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercarePickupContactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    contact = ser.save(school_fk_id=school_id, student_fk_id=student_id)
    return Response(AftercarePickupContactSerializer(contact).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=RosterTodayResponseSerializer)
@api_view(["GET"])
def roster_today(request):
    school_id = school_id_from_request(request, required=True)
    if not _has_permission(request, "extended_care.view"):
        return _forbidden()

    today = timezone.now().date()
    dow = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][today.weekday()]
    enroll_qs = (
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id,
            student_fk__isnull=False,
            is_active=True,
            start_date__lte=today,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .select_related("student_fk")
    )
    requested_session = request.query_params.get("care_session", "PM")
    if requested_session not in ("AM", "PM"):
        return _bad_request("Invalid care session.")
    enroll = [row for row in enroll_qs if row.care_session == requested_session and dow in (row.days_of_week or [])]
    attendance_map = {
        (row.student_fk_id, row.care_session): row
        for row in AftercareAttendance.objects.filter(school_fk_id=school_id, date=today, care_session=requested_session)
    }
    rows = [
        {
            "student_id": row.student_fk_id,
            "care_session": row.care_session,
            "enrollment": AftercareEnrollmentSerializer(row).data,
            "attendance": (
                AftercareAttendanceSerializer(attendance_map[(row.student_fk_id, row.care_session)]).data
                if (row.student_fk_id, row.care_session) in attendance_map else None
            ),
        }
        for row in enroll
    ]
    return Response({"date": str(today), "dow": dow, "care_session": requested_session, "rows": rows})


@extend_schema(request=AftercareCheckinRequestSerializer, responses={201: AftercareAttendanceSerializer})
@api_view(["POST"])
def checkin(request):
    school_id = school_id_from_request(request, required=True)
    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercareCheckinRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        attendance = checkin_student(
            school_id=school_id,
            student_id=ser.validated_data["student_id"],
            note=ser.validated_data.get("note", ""),
            care_session=ser.validated_data["care_session"],
        )
    except ValueError as exc:
        return _bad_request(exc)
    return Response(AftercareAttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)


@extend_schema(request=AftercareCheckoutRequestSerializer, responses={200: AftercareAttendanceSerializer})
@api_view(["POST"])
def checkout(request):
    school_id = school_id_from_request(request, required=True)
    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercareCheckoutRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        attendance = checkout_student(
            school_id=school_id,
            student_id=ser.validated_data["student_id"],
            pickup_contact_id=ser.validated_data["pickup_contact_id"],
            pickup_name_freeform=ser.validated_data.get("pickup_name_freeform", ""),
            pickup_verified=ser.validated_data["pickup_verified"],
            care_session=ser.validated_data["care_session"],
        )
    except (ValueError, AftercareAttendance.DoesNotExist) as exc:
        return _bad_request(exc)
    return Response(AftercareAttendanceSerializer(attendance).data)


class AftercareHandoffRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()

    def validate(self, attrs):
        # A staff identifier supplied by another operator is not an acknowledgement.
        if "receiving_staff_id" in self.initial_data:
            raise serializers.ValidationError(
                {"receiving_staff_id": "The receiving staff member must authenticate and acknowledge directly."}
            )
        return attrs


@extend_schema(request=AftercareHandoffRequestSerializer, responses={200: AftercareAttendanceSerializer})
@api_view(["POST"])
def school_handoff(request):
    school_id = school_id_from_request(request, required=True)
    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    serializer = AftercareHandoffRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        # Authenticated staff self-attestation: another user's ID is never accepted.
        attendance = handoff_student_to_school(
            school_id, serializer.validated_data["student_id"], request.user,
        )
    except ValueError:
        return _bad_request("A valid, authorized receiving staff acknowledgement is required.")
    return Response(AftercareAttendanceSerializer(attendance).data)


@extend_schema(methods=["GET"], responses=AftercareIncidentSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercareIncidentCreateRequestSerializer, responses={201: AftercareIncidentSerializer})
@api_view(["GET", "POST"])
def incidents(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _has_permission(request, "extended_care.view"):
            return _forbidden()
        qs = AftercareIncident.objects.filter(school_fk_id=school_id).order_by("-occurred_at")[:300]
        return Response(AftercareIncidentSerializer(qs, many=True).data)

    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercareIncidentCreateRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        incident = record_incident(
            school_id=school_id,
            student_id=ser.validated_data["student_id"],
            severity=ser.validated_data.get("severity", "MINOR"),
            description=ser.validated_data.get("description", ""),
            attendance_id=ser.validated_data.get("attendance_id"),
            parent_notified=ser.validated_data.get("parent_notified", False),
        )
    except AftercareIntegrationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
    except ValueError as exc:
        return _bad_request(exc)
    return Response(AftercareIncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=ParentViewResponseSerializer)
@api_view(["GET"])
def parent_view(request, student_id):
    school_id = school_id_from_request(request, required=True)
    if not _guardian_can_view_student(request, school_id=school_id, student_id=student_id):
        return _forbidden()
    enrollment = AftercareEnrollment.objects.filter(
        school_fk_id=school_id, student_fk_id=student_id, is_active=True
    ).first()
    attendance = AftercareAttendance.objects.filter(
        school_fk_id=school_id, student_fk_id=student_id
    ).order_by("-date", "care_session")[:60]
    return Response(
        {
            "enrollment": AftercareEnrollmentSerializer(enrollment).data if enrollment else None,
            "attendance": AftercareAttendanceSerializer(attendance, many=True).data,
        }
    )


@extend_schema(responses=BoardSummaryResponseSerializer)
@api_view(["GET"])
def board_summary(request):
    school_id = school_id_from_request(request, required=True)
    if not (
        _has_permission(request, "board.view")
        or _has_permission(request, "extended_care.view")
    ):
        return _forbidden()

    today = timezone.now().date()
    month_start = today.replace(day=1)
    care_session = request.query_params.get("care_session")
    if care_session is not None and care_session not in ("AM", "PM"):
        return _bad_request("Invalid care session.")
    enrollments = (
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id, student_fk__isnull=False,
            is_active=True, start_date__lte=today,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
    )
    attendance_qs = AftercareAttendance.objects.filter(
        school_fk_id=school_id, date__range=(month_start, today),
    )
    incidents_qs = AftercareIncident.objects.filter(
        school_fk_id=school_id,
        occurred_at__date__range=(month_start, today),
    )
    # An incident lacking an attendance link cannot reliably be attributed
    # to AM or PM; report it separately rather than copying it to both.
    unattributed_incidents = incidents_qs.filter(attendance_fk__isnull=True).count()
    if care_session:
        enrollments = enrollments.filter(care_session=care_session)
        attendance_qs = attendance_qs.filter(care_session=care_session)
        incidents_qs = incidents_qs.filter(
            attendance_fk__care_session=care_session,
            attendance_fk__school_fk_id=school_id,
        )
    active_enrollment = enrollments.values("student_fk_id").distinct().count()
    sessions = attendance_qs.count()
    late_pickups = attendance_qs.filter(late_minutes__gt=0).count()
    incidents_mtd = incidents_qs.count()
    late_fee_cents = attendance_qs.aggregate(total=Sum("late_fee_cents"))["total"] or 0
    return Response(
        {
            "care_session": care_session or "ALL",
            "as_of": str(today),
            "active_enrollment": active_enrollment,
            "sessions_mtd": sessions,
            "late_pickups_mtd": late_pickups,
            "incidents_mtd": incidents_mtd,
            "unattributed_incidents_mtd": unattributed_incidents,
            "late_fee_assessed_mtd": float(late_fee_cents) / 100.0,
            "late_fee_revenue_mtd": float(late_fee_cents) / 100.0,
        }
    )
