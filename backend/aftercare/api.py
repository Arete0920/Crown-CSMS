from django.db.models import Q, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import permission_school_from_request, user_has_permission
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
from .services import checkin_student, checkout_student, ensure_config, record_incident
from .tenant import school_id_from_request


class RosterTodayRowSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
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
    sessions_mtd = serializers.IntegerField()
    late_pickups_mtd = serializers.IntegerField()
    incidents_mtd = serializers.IntegerField()
    late_fee_revenue_mtd = serializers.FloatField()


class AftercareCheckinRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    note = serializers.CharField(required=False, allow_blank=True)


class AftercareCheckoutRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    pickup_contact_id = serializers.IntegerField(required=False, allow_null=True)
    pickup_name_freeform = serializers.CharField(required=False, allow_blank=True)
    pickup_verified = serializers.BooleanField(required=False)


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
    return user_has_permission(user, code, school=permission_school_from_request(request))


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
    if not _canonical_student_exists(school_id=school_id, student_id=student_id):
        return _bad_request("Student is not active in this school.")
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
    enroll = [row for row in enroll_qs if dow in (row.days_of_week or [])]
    attendance_map = {
        row.student_fk_id: row
        for row in AftercareAttendance.objects.filter(school_fk_id=school_id, date=today)
    }
    rows = [
        {
            "student_id": row.student_fk_id,
            "enrollment": AftercareEnrollmentSerializer(row).data,
            "attendance": (
                AftercareAttendanceSerializer(attendance_map[row.student_fk_id]).data
                if row.student_fk_id in attendance_map else None
            ),
        }
        for row in enroll
    ]
    return Response({"date": str(today), "dow": dow, "rows": rows})


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
            pickup_contact_id=ser.validated_data.get("pickup_contact_id"),
            pickup_name_freeform=ser.validated_data.get("pickup_name_freeform", ""),
            pickup_verified=ser.validated_data.get("pickup_verified", False),
        )
    except (ValueError, AftercareAttendance.DoesNotExist) as exc:
        return _bad_request(exc)
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
    ).order_by("-date")[:30]
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
    active_enrollment = AftercareEnrollment.objects.filter(school_fk_id=school_id, is_active=True).count()
    sessions = AftercareAttendance.objects.filter(school_fk_id=school_id, date__gte=month_start).count()
    late_pickups = AftercareAttendance.objects.filter(
        school_fk_id=school_id, date__gte=month_start, late_minutes__gt=0
    ).count()
    incidents_mtd = AftercareIncident.objects.filter(
        school_fk_id=school_id, occurred_at__date__gte=month_start
    ).count()
    late_fee_cents = (
        AftercareAttendance.objects.filter(school_fk_id=school_id, date__gte=month_start)
        .aggregate(total=Sum("late_fee_cents"))["total"]
        or 0
    )
    return Response(
        {
            "as_of": str(today),
            "active_enrollment": active_enrollment,
            "sessions_mtd": sessions,
            "late_pickups_mtd": late_pickups,
            "incidents_mtd": incidents_mtd,
            "late_fee_revenue_mtd": float(late_fee_cents) / 100.0,
        }
    )
