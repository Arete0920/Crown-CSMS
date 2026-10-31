from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
from subscriptions.gates import school_has_module
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
from .services import care_timezone, checkin_student, checkout_student, ensure_config, handoff_student_to_school, record_incident, school_local_date
from .tenant import school_id_from_request


class RosterTodayRowSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    care_session = serializers.ChoiceField(choices=["AM", "PM"])
    enrollment = AftercareEnrollmentSerializer(allow_null=True)
    attendance = AftercareAttendanceSerializer(allow_null=True)
    unscheduled = serializers.BooleanField()


class RosterTodayResponseSerializer(serializers.Serializer):
    date = serializers.CharField()
    dow = serializers.CharField()
    care_session = serializers.ChoiceField(choices=["AM", "PM"])
    rows = RosterTodayRowSerializer(many=True)
    unlinked_attendance_count = serializers.IntegerField()


class ParentViewResponseSerializer(serializers.Serializer):
    enrollment = AftercareEnrollmentSerializer(allow_null=True)
    enrollments = AftercareEnrollmentSerializer(many=True)
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
    # Legacy response key: null until actual settled receipts can be proven.
    late_fee_revenue_mtd = serializers.FloatField(allow_null=True)


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


CARE_SESSION_MODULES = {"AM": "before_care", "PM": "after_care"}


def _entitled_sessions(school_id):
    """Exact-session, tenant-scoped licenses; Diadem is not an implicit bundle."""
    return tuple(
        session for session, module in CARE_SESSION_MODULES.items()
        if school_has_module(school_id, module)
    )


def _module_denied():
    return Response(
        {"detail": "The care module is not enabled for this tenant.",
         "code": "CARE_MODULE_NOT_ENABLED"},
        status=status.HTTP_403_FORBIDDEN,
    )


def _session_denial(school_id, session):
    if session not in CARE_SESSION_MODULES or not school_has_module(
        school_id, CARE_SESSION_MODULES[session]
    ):
        return _module_denied()
    return None


@extend_schema(methods=["GET"], responses=AftercareProgramConfigSerializer)
@extend_schema(methods=["PUT"], request=AftercareProgramConfigSerializer, responses=AftercareProgramConfigSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "PUT"])
def program_config(request):
    school_id = school_id_from_request(request, required=True)
    if not _entitled_sessions(school_id):
        return _module_denied()
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
        entitled = _entitled_sessions(school_id)
        if not entitled:
            return _module_denied()
        requested_session = request.query_params.get("care_session")
        if requested_session is not None and requested_session not in CARE_SESSION_MODULES:
            return _bad_request("Invalid care session.")
        if requested_session is not None:
            if requested_session not in entitled:
                return _module_denied()
            entitled = (requested_session,)
        qs = AftercareEnrollment.objects.filter(
            school_fk_id=school_id, care_session__in=entitled,
        ).order_by("-created_at")[:500]
        return Response(AftercareEnrollmentSerializer(qs, many=True).data)

    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercareEnrollmentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    denied = _session_denial(school_id, ser.validated_data.get("care_session", "PM"))
    if denied is not None:
        return denied
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
    if not _entitled_sessions(school_id):
        return _module_denied()
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

    try:
        today = school_local_date(school_id, timezone.now())
    except ValueError as exc:
        return _bad_request(exc)
    dow = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][today.weekday()]
    enroll_qs = (
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id,
            student_fk__isnull=False,
            student_fk__school_id=school_id,
            student_fk__is_active=True,
            is_active=True,
            start_date__lte=today,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .select_related("student_fk")
    )
    requested_session = request.query_params.get("care_session", "PM")
    if requested_session not in ("AM", "PM"):
        return _bad_request("Invalid care session.")
    denied = _session_denial(school_id, requested_session)
    if denied is not None:
        return denied
    enroll = [row for row in enroll_qs if row.care_session == requested_session and dow in (row.days_of_week or [])]
    # Custody records must remain visible after an enrollment is suspended,
    # expired, deactivated, or its student profile has become inactive.
    attendance_records = list(
        AftercareAttendance.objects.filter(
            school_fk_id=school_id, date=today, care_session=requested_session,
        ).select_related("student_fk")
    )
    attendance_map = {row.student_fk_id: row for row in attendance_records if row.student_fk_id}
    scheduled_student_ids = {row.student_fk_id for row in enroll}
    rows = [
        {
            "student_id": row.student_fk_id,
            "student_name": (row.student_fk.first_name + " " + row.student_fk.last_name).strip(),
            "care_session": row.care_session,
            "enrollment": AftercareEnrollmentSerializer(row).data,
            "attendance": (
                AftercareAttendanceSerializer(attendance_map[row.student_fk_id]).data
                if row.student_fk_id in attendance_map else None
            ),
            "unscheduled": False,
        }
        for row in enroll
    ]
    unlinked_attendance_count = 0
    for attendance in attendance_records:
        if attendance.student_fk_id in scheduled_student_ids:
            continue
        student = attendance.student_fk
        if student is None or student.school_id != school_id:
            # Never disclose another tenant's student identity through a
            # malformed historical attendance FK. Count for operator review.
            unlinked_attendance_count += 1
            continue
        rows.append({
            "student_id": student.pk,
            "student_name": (student.first_name + " " + student.last_name).strip(),
            "care_session": requested_session,
            "enrollment": None,
            "attendance": AftercareAttendanceSerializer(attendance).data,
            "unscheduled": True,
        })
    return Response({
        "date": str(today), "dow": dow, "care_session": requested_session,
        "rows": rows, "unlinked_attendance_count": unlinked_attendance_count,
    })


@extend_schema(request=AftercareCheckinRequestSerializer, responses={201: AftercareAttendanceSerializer})
@api_view(["POST"])
def checkin(request):
    school_id = school_id_from_request(request, required=True)
    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    ser = AftercareCheckinRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    denied = _session_denial(school_id, ser.validated_data["care_session"])
    if denied is not None:
        return denied
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
    denied = _session_denial(school_id, ser.validated_data["care_session"])
    if denied is not None:
        return denied
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
    denied = _session_denial(school_id, "AM")
    if denied is not None:
        return denied
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
    entitled = _entitled_sessions(school_id)
    if request.method == "GET":
        if not _has_permission(request, "extended_care.view"):
            return _forbidden()
        if not entitled:
            return _module_denied()
        requested = request.query_params.get("care_session")
        if requested is not None and requested not in CARE_SESSION_MODULES:
            return _bad_request("Invalid care session.")
        if requested is not None and requested not in entitled:
            return _module_denied()
        if requested is None and len(entitled) == 1:
            requested = entitled[0]
        qs = AftercareIncident.objects.filter(school_fk_id=school_id)
        if requested:
            qs = qs.filter(
                attendance_fk__care_session=requested,
                attendance_fk__school_fk_id=school_id,
            )
        return Response(AftercareIncidentSerializer(
            qs.order_by("-occurred_at")[:300], many=True,
        ).data)

    if not _has_permission(request, "extended_care.edit"):
        return _forbidden()
    if not entitled:
        return _module_denied()
    ser = AftercareIncidentCreateRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    attendance_id = ser.validated_data.get("attendance_id")
    if attendance_id is not None:
        session = AftercareAttendance.objects.filter(
            pk=attendance_id, school_fk_id=school_id,
        ).values_list("care_session", flat=True).first()
        if session is None:
            return _bad_request("Care attendance not found in this tenant.")
        if session not in entitled:
            return _module_denied()
    elif len(entitled) != 2:
        # An unlinked incident cannot be safely attributed to AM versus PM.
        return _bad_request("Care session attribution requires an attendance record.")
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
    entitled = _entitled_sessions(school_id)
    if not entitled:
        return _module_denied()
    # Preserve the PM-first legacy field while exposing the authoritative
    # full AM/PM enrollment set for family portals. One child is not two profiles.
    enrollments = list(
        AftercareEnrollment.objects.filter(
            school_fk_id=school_id, student_fk_id=student_id, is_active=True,
            care_session__in=entitled,
        ).order_by("care_session", "-start_date", "-created_at")
    )
    legacy_enrollment = next(
        (row for row in enrollments if row.care_session == "PM"),
        enrollments[0] if enrollments else None,
    )
    attendance = AftercareAttendance.objects.filter(
        school_fk_id=school_id, student_fk_id=student_id,
        care_session__in=entitled,
    ).order_by("-date", "care_session")[:60]
    return Response(
        {
            "enrollment": (
                AftercareEnrollmentSerializer(legacy_enrollment).data
                if legacy_enrollment else None
            ),
            "enrollments": AftercareEnrollmentSerializer(enrollments, many=True).data,
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

    try:
        local_tz = care_timezone(school_id)
        today = timezone.now().astimezone(local_tz).date()
    except ValueError as exc:
        return _bad_request(exc)
    month_start = today.replace(day=1)
    # Use actual instant boundaries so incidents near UTC midnight are
    # counted in the right tenant-local reporting month and day.
    month_start_at = timezone.make_aware(datetime.combine(month_start, time.min), timezone=local_tz)
    tomorrow_at = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min), timezone=local_tz)
    care_session = request.query_params.get("care_session")
    if care_session is not None and care_session not in ("AM", "PM"):
        return _bad_request("Invalid care session.")
    entitled = _entitled_sessions(school_id)
    if not entitled:
        return _module_denied()
    if care_session is not None and care_session not in entitled:
        return _module_denied()
    if care_session is None and len(entitled) == 1:
        care_session = entitled[0]
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
        occurred_at__gte=month_start_at,
        occurred_at__lt=tomorrow_at,
    )
    # An incident lacking an attendance link cannot reliably be attributed
    # to AM or PM; report it separately rather than copying it to both.
    unattributed_incidents = (
        incidents_qs.filter(attendance_fk__isnull=True).count() if len(entitled) == 2 else 0
    )
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
            # Assessment is not a settled payment; never report as revenue.
            "late_fee_revenue_mtd": None,
        }
    )
