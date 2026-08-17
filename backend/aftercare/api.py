from uuid import UUID

from django.db.models import Q, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
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
    severity = serializers.ChoiceField(choices=["MINOR", "MODERATE", "MAJOR"], required=False)
    description = serializers.CharField()
    attendance_id = serializers.IntegerField(required=False, allow_null=True)
    parent_notified = serializers.BooleanField(required=False)


def _staff_authorized(request) -> bool:
    user = getattr(request, "user", None)
    school = getattr(request, "school", None)
    return bool(user and getattr(user, "is_authenticated", False) and school is not None and user_has_permission(user, "extended_care.view", school=school))


def _board_authorized(request) -> bool:
    user = getattr(request, "user", None)
    school = getattr(request, "school", None)
    return bool(user and getattr(user, "is_authenticated", False) and school is not None and user_has_permission(user, "board.view", school=school))


def _guardian_authorized(request, school_id: UUID, student_id: UUID) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return AftercareEnrollment.objects.filter(school_fk_id=school_id, student_fk_id=student_id, student_fk__household__guardians__account=user, is_active=True).exists()


def _staff_or_guardian(request, school_id: UUID, student_id: UUID) -> bool:
    return _staff_authorized(request) or _guardian_authorized(request, school_id, student_id)


@extend_schema(methods=["GET"], responses=AftercareProgramConfigSerializer)
@extend_schema(methods=["PUT"], request=AftercareProgramConfigSerializer, responses=AftercareProgramConfigSerializer)
@api_view(["GET", "PUT"])
def program_config(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    cfg = ensure_config(school_id)
    if request.method == "GET":
        return Response(AftercareProgramConfigSerializer(cfg).data)
    ser = AftercareProgramConfigSerializer(cfg, data=request.data, partial=True, context={"request": request})
    ser.is_valid(raise_exception=True)
    ser.save(school_fk_id=school_id, school_id=None)
    return Response(ser.data)


@extend_schema(methods=["GET"], responses=AftercareEnrollmentSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercareEnrollmentSerializer, responses=AftercareEnrollmentSerializer)
@api_view(["GET", "POST"])
def enrollments(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        qs = AftercareEnrollment.objects.filter(school_fk_id=school_id).order_by("-created_at")[:500]
        return Response(AftercareEnrollmentSerializer(qs, many=True).data)
    ser = AftercareEnrollmentSerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)
    student = ser.validated_data["student_fk"]
    ser.save(school_fk_id=school_id, student_fk=student, school_id=None, student_id=None)
    return Response(ser.data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=AftercarePickupContactSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercarePickupContactSerializer, responses=AftercarePickupContactSerializer)
@api_view(["GET", "POST"])
def pickup_contacts(request, student_id: UUID):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _staff_or_guardian(request, school_id, student_id):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        qs = AftercarePickupContact.objects.filter(school_fk_id=school_id, student_fk_id=student_id, is_active=True)
        return Response(AftercarePickupContactSerializer(qs, many=True).data)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if not AftercareEnrollment.objects.filter(school_fk_id=school_id, student_fk_id=student_id, is_active=True).exists():
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    ser = AftercarePickupContactSerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)
    ser.save(school_fk_id=school_id, student_fk_id=student_id, school_id=None, student_id=None)
    return Response(ser.data, status=status.HTTP_201_CREATED)


@extend_schema(responses=RosterTodayResponseSerializer)
@api_view(["GET"])
def roster_today(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    today = timezone.localdate()
    dow = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][today.weekday()]
    enroll_qs = AftercareEnrollment.objects.filter(school_fk_id=school_id, student_fk__isnull=False, is_active=True, start_date__lte=today).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
    enroll = [row for row in enroll_qs if dow in (row.days_of_week or [])]
    attendance_map = {row.student_fk_id: row for row in AftercareAttendance.objects.filter(school_fk_id=school_id, date=today)}
    rows = [{"student_id": row.student_fk_id, "enrollment": AftercareEnrollmentSerializer(row).data, "attendance": AftercareAttendanceSerializer(attendance_map.get(row.student_fk_id)).data if attendance_map.get(row.student_fk_id) else None} for row in enroll]
    return Response({"date": str(today), "dow": dow, "rows": rows})


@extend_schema(request=AftercareCheckinRequestSerializer, responses={201: AftercareAttendanceSerializer})
@api_view(["POST"])
def checkin(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    payload = AftercareCheckinRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    student_id = payload.validated_data["student_id"]
    if not AftercareEnrollment.objects.filter(school_fk_id=school_id, student_fk_id=student_id, is_active=True).exists():
        return Response({"detail": "Student not enrolled."}, status=status.HTTP_404_NOT_FOUND)
    attendance = checkin_student(school_id=school_id, student_id=student_id, note=payload.validated_data.get("note", ""))
    return Response(AftercareAttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)


@extend_schema(request=AftercareCheckoutRequestSerializer, responses={200: AftercareAttendanceSerializer})
@api_view(["POST"])
def checkout(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    payload = AftercareCheckoutRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    student_id = payload.validated_data["student_id"]
    contact_id = payload.validated_data.get("pickup_contact_id")
    if contact_id is not None and not AftercarePickupContact.objects.filter(pk=contact_id, school_fk_id=school_id, student_fk_id=student_id, is_active=True).exists():
        return Response({"detail": "Pickup contact not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        attendance = checkout_student(school_id=school_id, student_id=student_id, pickup_contact_id=contact_id, pickup_name_freeform=payload.validated_data.get("pickup_name_freeform", ""), pickup_verified=payload.validated_data.get("pickup_verified", False))
    except AftercareAttendance.DoesNotExist:
        return Response({"detail": "Active attendance not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(AftercareAttendanceSerializer(attendance).data)


@extend_schema(methods=["GET"], responses=AftercareIncidentSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercareIncidentCreateRequestSerializer, responses={201: AftercareIncidentSerializer})
@api_view(["GET", "POST"])
def incidents(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        qs = AftercareIncident.objects.filter(school_fk_id=school_id).order_by("-occurred_at")[:300]
        return Response(AftercareIncidentSerializer(qs, many=True).data)
    payload = AftercareIncidentCreateRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    student_id = payload.validated_data["student_id"]
    if not AftercareEnrollment.objects.filter(school_fk_id=school_id, student_fk_id=student_id).exists():
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    incident = record_incident(school_id=school_id, student_id=student_id, severity=payload.validated_data.get("severity", "MINOR"), description=payload.validated_data["description"], attendance_id=payload.validated_data.get("attendance_id"), parent_notified=payload.validated_data.get("parent_notified", False))
    return Response(AftercareIncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=ParentViewResponseSerializer)
@api_view(["GET"])
def parent_view(request, student_id: UUID):
    school_id = school_id_from_request(request, required=True)
    if not _staff_or_guardian(request, school_id, student_id):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    enrollment = AftercareEnrollment.objects.filter(school_fk_id=school_id, student_fk_id=student_id, is_active=True).first()
    attendance = AftercareAttendance.objects.filter(school_fk_id=school_id, student_fk_id=student_id).order_by("-date")[:30]
    return Response({"enrollment": AftercareEnrollmentSerializer(enrollment).data if enrollment else None, "attendance": AftercareAttendanceSerializer(attendance, many=True).data})


@extend_schema(responses=BoardSummaryResponseSerializer)
@api_view(["GET"])
def board_summary(request):
    school_id = school_id_from_request(request, required=True)
    if not (_board_authorized(request) or _staff_authorized(request)):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    today = timezone.localdate()
    month_start = today.replace(day=1)
    active_enrollment = AftercareEnrollment.objects.filter(school_fk_id=school_id, is_active=True).count()
    sessions = AftercareAttendance.objects.filter(school_fk_id=school_id, date__gte=month_start).count()
    late_pickups = AftercareAttendance.objects.filter(school_fk_id=school_id, date__gte=month_start, late_minutes__gt=0).count()
    incidents_mtd = AftercareIncident.objects.filter(school_fk_id=school_id, occurred_at__date__gte=month_start).count()
    late_fee_cents = AftercareAttendance.objects.filter(school_fk_id=school_id, date__gte=month_start).aggregate(total=Sum("late_fee_cents"))["total"] or 0
    return Response({"as_of": str(today), "active_enrollment": active_enrollment, "sessions_mtd": sessions, "late_pickups_mtd": late_pickups, "incidents_mtd": incidents_mtd, "late_fee_revenue_mtd": float(late_fee_cents) / 100.0})
