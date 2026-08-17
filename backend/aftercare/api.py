from django.db.models import Q, Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes

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
    student_id = serializers.IntegerField()
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
    student_id = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True)


class AftercareCheckoutRequestSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    pickup_contact_id = serializers.IntegerField(required=False, allow_null=True)
    pickup_name_freeform = serializers.CharField(required=False, allow_blank=True)
    pickup_verified = serializers.BooleanField(required=False)


class AftercareIncidentCreateRequestSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    severity = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    attendance_id = serializers.IntegerField(required=False, allow_null=True)
    parent_notified = serializers.BooleanField(required=False)


class AftercareStudentRequiredSerializer(serializers.Serializer):
    detail = serializers.CharField()


def _staff_authorized(request) -> bool:
    user = getattr(request, "user", None)
    school = getattr(request, "school", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and school is not None
        and user_has_permission(user, "extended_care.view", school=school)
    )


def _board_authorized(request) -> bool:
    user = getattr(request, "user", None)
    school = getattr(request, "school", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and school is not None
        and user_has_permission(user, "board.view", school=school)
    )


def require_role(request, allowed_roles: set) -> bool:
    """Compatibility helper backed only by persistent tenant-scoped CROWN permissions."""
    normalized = {str(role).lower() for role in allowed_roles}
    if "board" in normalized and _board_authorized(request):
        return True
    if normalized.intersection({"admin", "aftercare_staff"}) and _staff_authorized(request):
        return True
    return False


def _guardian_authorized(request, school_id: int, student_id: int) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return AftercareEnrollment.objects.filter(
        school_id=school_id,
        student_id=student_id,
        student_fk__school_id=getattr(getattr(request, "school", None), "id", None),
        student_fk__household__guardians__account=user,
    ).exists()


def _staff_or_guardian(request, school_id: int, student_id: int) -> bool:
    return _staff_authorized(request) or _guardian_authorized(request, school_id, student_id)


@extend_schema(methods=["GET"], responses=AftercareProgramConfigSerializer)
@extend_schema(methods=["PUT"], request=AftercareProgramConfigSerializer, responses=AftercareProgramConfigSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "PUT"])
def program_config(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    cfg = ensure_config(school_id)
    if request.method == "GET":
        return Response(AftercareProgramConfigSerializer(cfg).data)
    ser = AftercareProgramConfigSerializer(cfg, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save(school_id=school_id)
    return Response(ser.data)


@extend_schema(methods=["GET"], responses=AftercareEnrollmentSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercareEnrollmentSerializer, responses=AftercareEnrollmentSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
def enrollments(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        qs = AftercareEnrollment.objects.filter(school_id=school_id).order_by("-created_at")[:500]
        return Response(AftercareEnrollmentSerializer(qs, many=True).data)
    ser = AftercareEnrollmentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    student_fk = ser.validated_data.get("student_fk")
    if student_fk is not None and str(student_fk.school_id) != str(getattr(request.school, "id", "")):
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    ser.save(school_id=school_id)
    return Response(ser.data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=AftercarePickupContactSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercarePickupContactSerializer, responses=AftercarePickupContactSerializer)
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
def pickup_contacts(request, student_id: int):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not _staff_or_guardian(request, school_id, student_id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = AftercarePickupContact.objects.filter(school_id=school_id, student_id=student_id, is_active=True)
        return Response(AftercarePickupContactSerializer(qs, many=True).data)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    ser = AftercarePickupContactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save(school_id=school_id, student_id=student_id)
    return Response(ser.data, status=status.HTTP_201_CREATED)


@extend_schema(responses=RosterTodayResponseSerializer)
@api_view(["GET"])
def roster_today(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    today = timezone.now().date()
    dow = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][today.weekday()]
    enroll_qs = AftercareEnrollment.objects.filter(school_id=school_id, is_active=True, start_date__lte=today).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    enroll = [enrollment for enrollment in enroll_qs if dow in (enrollment.days_of_week or [])]
    attendance_map = {
        attendance.student_id: attendance
        for attendance in AftercareAttendance.objects.filter(school_id=school_id, date=today)
    }
    rows = [
        {
            "student_id": enrollment.student_id,
            "enrollment": AftercareEnrollmentSerializer(enrollment).data,
            "attendance": AftercareAttendanceSerializer(attendance_map.get(enrollment.student_id)).data
            if attendance_map.get(enrollment.student_id)
            else None,
        }
        for enrollment in enroll
    ]
    return Response({"date": str(today), "dow": dow, "rows": rows})


@extend_schema(request=AftercareCheckinRequestSerializer, responses={201: AftercareAttendanceSerializer, 400: AftercareStudentRequiredSerializer})
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def checkin(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    student_id = int(request.data.get("student_id", 0))
    if not student_id:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)
    if not AftercareEnrollment.objects.filter(school_id=school_id, student_id=student_id, is_active=True).exists():
        return Response({"detail": "Student not enrolled."}, status=status.HTTP_404_NOT_FOUND)
    attendance = checkin_student(school_id=school_id, student_id=student_id, note=request.data.get("note", ""))
    return Response(AftercareAttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)


@extend_schema(request=AftercareCheckoutRequestSerializer, responses={200: AftercareAttendanceSerializer, 400: AftercareStudentRequiredSerializer})
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def checkout(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    student_id = int(request.data.get("student_id", 0))
    if not student_id:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)
    raw_contact_id = request.data.get("pickup_contact_id")
    if raw_contact_id and not AftercarePickupContact.objects.filter(
        pk=int(raw_contact_id), school_id=school_id, student_id=student_id, is_active=True
    ).exists():
        return Response({"detail": "Pickup contact not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        attendance = checkout_student(
            school_id=school_id,
            student_id=student_id,
            pickup_contact_id=int(raw_contact_id) if raw_contact_id else None,
            pickup_name_freeform=request.data.get("pickup_name_freeform", "") or "",
            pickup_verified=bool(request.data.get("pickup_verified", False)),
        )
    except AftercareAttendance.DoesNotExist:
        return Response({"detail": "Active attendance not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(AftercareAttendanceSerializer(attendance).data, status=status.HTTP_200_OK)


@extend_schema(methods=["GET"], responses=AftercareIncidentSerializer(many=True))
@extend_schema(methods=["POST"], request=AftercareIncidentCreateRequestSerializer, responses={201: AftercareIncidentSerializer, 400: AftercareStudentRequiredSerializer})
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
def incidents(request):
    school_id = school_id_from_request(request, required=True)
    if not _staff_authorized(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        qs = AftercareIncident.objects.filter(school_id=school_id).order_by("-occurred_at")[:300]
        return Response(AftercareIncidentSerializer(qs, many=True).data)
    student_id = int(request.data.get("student_id", 0))
    if not student_id:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)
    if not AftercareEnrollment.objects.filter(school_id=school_id, student_id=student_id).exists():
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    raw_attendance_id = request.data.get("attendance_id")
    if raw_attendance_id and not AftercareAttendance.objects.filter(
        pk=int(raw_attendance_id), school_id=school_id, student_id=student_id
    ).exists():
        return Response({"detail": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
    incident = record_incident(
        school_id=school_id,
        student_id=student_id,
        severity=request.data.get("severity", "MINOR"),
        description=request.data.get("description", ""),
        attendance_id=int(raw_attendance_id) if raw_attendance_id else None,
        parent_notified=bool(request.data.get("parent_notified", False)),
    )
    return Response(AftercareIncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=ParentViewResponseSerializer)
@api_view(["GET"])
def parent_view(request, student_id: int):
    school_id = school_id_from_request(request, required=True)
    if not _staff_or_guardian(request, school_id, student_id):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    enrollment = AftercareEnrollment.objects.filter(school_id=school_id, student_id=student_id, is_active=True).first()
    attendance = AftercareAttendance.objects.filter(school_id=school_id, student_id=student_id).order_by("-date")[:30]
    return Response({
        "enrollment": AftercareEnrollmentSerializer(enrollment).data if enrollment else None,
        "attendance": AftercareAttendanceSerializer(attendance, many=True).data,
    })


@extend_schema(responses=BoardSummaryResponseSerializer)
@api_view(["GET"])
def board_summary(request):
    school_id = school_id_from_request(request, required=True)
    if not (_board_authorized(request) or _staff_authorized(request)):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    today = timezone.now().date()
    month_start = today.replace(day=1)
    active_enrollment = AftercareEnrollment.objects.filter(school_id=school_id, is_active=True).count()
    sessions = AftercareAttendance.objects.filter(school_id=school_id, date__gte=month_start).count()
    late_pickups = AftercareAttendance.objects.filter(school_id=school_id, date__gte=month_start, late_minutes__gt=0).count()
    incidents_mtd = AftercareIncident.objects.filter(school_id=school_id, occurred_at__date__gte=month_start).count()
    late_fee_cents = AftercareAttendance.objects.filter(school_id=school_id, date__gte=month_start).aggregate(total=Sum("late_fee_cents"))["total"] or 0
    return Response({
        "as_of": str(today),
        "active_enrollment": active_enrollment,
        "sessions_mtd": sessions,
        "late_pickups_mtd": late_pickups,
        "incidents_mtd": incidents_mtd,
        "late_fee_revenue_mtd": float(late_fee_cents) / 100.0,
    })
