from django.db.models import Sum, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
from .tenant import school_id_from_request
from .models import (
    AftercareEnrollment,
    AftercarePickupContact,
    AftercareAttendance,
    AftercareIncident,
)
from .serializers import (
    AftercareProgramConfigSerializer,
    AftercareEnrollmentSerializer,
    AftercarePickupContactSerializer,
    AftercareAttendanceSerializer,
    AftercareIncidentSerializer,
)
from .services import ensure_config, checkin_student, checkout_student, record_incident


class AftercareApiErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


def require_role(request, allowed_roles: set) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    school = getattr(request, "school", None)
    normalized = {str(r).lower() for r in allowed_roles}

    if "board" in normalized and user_has_permission(user, "board.view", school=school):
        return True

    if normalized.intersection({"admin", "aftercare_staff"}):
        if user_has_permission(user, "aftercare.edit", school=school):
            return True
        if user_has_permission(user, "aftercare.view", school=school):
            return True

    return False


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@api_view(["GET", "PUT"])
def program_config(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        cfg = ensure_config(school_id)
        return Response(AftercareProgramConfigSerializer(cfg).data)

    if not require_role(request, {"admin"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    cfg = ensure_config(school_id)
    ser = AftercareProgramConfigSerializer(cfg, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save(school_id=school_id)
    return Response(ser.data)


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="aftercare_enrollments",
    tags=["Enrollment"],
    request=AftercareEnrollmentSerializer,
    responses={
        200: AftercareEnrollmentSerializer(many=True),
        201: AftercareEnrollmentSerializer,
        403: AftercareApiErrorSerializer,
    },
)
@api_view(["GET", "POST"])
def enrollments(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        qs = AftercareEnrollment.objects.filter(school_id=school_id).order_by("-created_at")[:500]
        return Response(AftercareEnrollmentSerializer(qs, many=True).data)

    if not require_role(request, {"admin"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    ser = AftercareEnrollmentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save(school_id=school_id)
    return Response(ser.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Pickup contacts
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def pickup_contacts(request, student_id: int):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        qs = AftercarePickupContact.objects.filter(
            school_id=school_id, student_id=student_id, is_active=True
        )
        return Response(AftercarePickupContactSerializer(qs, many=True).data)

    if not require_role(request, {"admin", "aftercare_staff"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    ser = AftercarePickupContactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save(school_id=school_id, student_id=student_id)
    return Response(ser.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

@api_view(["GET"])
def roster_today(request):
    """Students enrolled for today, with their check-in/out state."""
    school_id = school_id_from_request(request, required=True)
    if not require_role(request, {"admin", "aftercare_staff"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.now().date()
    dow = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][today.weekday()]

    enroll_qs = AftercareEnrollment.objects.filter(
        school_id=school_id,
        is_active=True,
        start_date__lte=today,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    # Day-of-week filter (stored as JSON array)
    enroll = [e for e in enroll_qs if dow in (e.days_of_week or [])]

    att_map = {a.student_id: a for a in AftercareAttendance.objects.filter(school_id=school_id, date=today)}

    rows = []
    for e in enroll:
        a = att_map.get(e.student_id)
        rows.append({
            "student_id": e.student_id,
            "enrollment": AftercareEnrollmentSerializer(e).data,
            "attendance": AftercareAttendanceSerializer(a).data if a else None,
        })

    return Response({"date": str(today), "dow": dow, "rows": rows})


# ---------------------------------------------------------------------------
# Check-in / Check-out
# ---------------------------------------------------------------------------

@api_view(["POST"])
def checkin(request):
    school_id = school_id_from_request(request, required=True)
    if not require_role(request, {"admin", "aftercare_staff"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    student_id = int(request.data.get("student_id", 0))
    if not student_id:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)

    a = checkin_student(school_id=school_id, student_id=student_id, note=request.data.get("note", ""))
    return Response(AftercareAttendanceSerializer(a).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def checkout(request):
    school_id = school_id_from_request(request, required=True)
    if not require_role(request, {"admin", "aftercare_staff"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    student_id = int(request.data.get("student_id", 0))
    if not student_id:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)

    raw_contact_id = request.data.get("pickup_contact_id")
    a = checkout_student(
        school_id=school_id,
        student_id=student_id,
        pickup_contact_id=int(raw_contact_id) if raw_contact_id else None,
        pickup_name_freeform=request.data.get("pickup_name_freeform", "") or "",
        pickup_verified=bool(request.data.get("pickup_verified", False)),
    )
    return Response(AftercareAttendanceSerializer(a).data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def incidents(request):
    school_id = school_id_from_request(request, required=True)
    if not require_role(request, {"admin", "aftercare_staff"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        qs = AftercareIncident.objects.filter(school_id=school_id).order_by("-occurred_at")[:300]
        return Response(AftercareIncidentSerializer(qs, many=True).data)

    student_id = int(request.data.get("student_id", 0))
    if not student_id:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)

    raw_att_id = request.data.get("attendance_id")
    inc = record_incident(
        school_id=school_id,
        student_id=student_id,
        severity=request.data.get("severity", "MINOR"),
        description=request.data.get("description", ""),
        attendance_id=int(raw_att_id) if raw_att_id else None,
        parent_notified=bool(request.data.get("parent_notified", False)),
    )
    return Response(AftercareIncidentSerializer(inc).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Parent view
# ---------------------------------------------------------------------------

@api_view(["GET"])
def parent_view(request, student_id: int):
    """
    Parent-facing read-only summary: enrollment + attendance history (last 30).
    """
    school_id = school_id_from_request(request, required=True)
    if not require_role(request, {"admin", "aftercare_staff", "board"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    enr = AftercareEnrollment.objects.filter(
        school_id=school_id, student_id=student_id, is_active=True
    ).first()
    att = AftercareAttendance.objects.filter(
        school_id=school_id, student_id=student_id
    ).order_by("-date")[:30]

    return Response({
        "enrollment": AftercareEnrollmentSerializer(enr).data if enr else None,
        "attendance": AftercareAttendanceSerializer(att, many=True).data,
    })


# ---------------------------------------------------------------------------
# Board summary (read-only, no student identifiers)
# ---------------------------------------------------------------------------

@api_view(["GET"])
def board_summary(request):
    """Board governance summary — enrollment counts + MTD stats only, no PII."""
    school_id = school_id_from_request(request, required=True)
    if not require_role(request, {"board", "admin"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.now().date()
    month_start = today.replace(day=1)

    active_enroll = AftercareEnrollment.objects.filter(school_id=school_id, is_active=True).count()
    sessions = AftercareAttendance.objects.filter(school_id=school_id, date__gte=month_start).count()
    late = AftercareAttendance.objects.filter(
        school_id=school_id, date__gte=month_start, late_minutes__gt=0
    ).count()
    incidents_mtd = AftercareIncident.objects.filter(
        school_id=school_id, occurred_at__date__gte=month_start
    ).count()
    late_fee_cents = (
        AftercareAttendance.objects.filter(school_id=school_id, date__gte=month_start)
        .aggregate(total=Sum("late_fee_cents"))["total"] or 0
    )

    return Response({
        "as_of": str(today),
        "active_enrollment": active_enroll,
        "sessions_mtd": sessions,
        "late_pickups_mtd": late,
        "incidents_mtd": incidents_mtd,
        "late_fee_revenue_mtd": float(late_fee_cents) / 100.0,
    })
