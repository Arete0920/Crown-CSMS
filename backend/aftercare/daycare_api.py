"""Authenticated standalone Diadem API; isolated from AM/PM Extended Care.

Staff identity and tenant come exclusively from the authenticated principal.
No site, child, actor or guardian information supplied by a client can override
the server-side tenant, staff RBAC, verified coverage, or custody grants.

These routes use synchronous, transaction-protected services; they do not
activate childcare licensing or authorize production operations.
"""
from __future__ import annotations

from uuid import UUID
from django.db.models import F

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import School
from core.permissions import user_has_permission
from .daycare_checkin import CheckinRefused, checkin_child
from .daycare_release import ReleaseRefused, release_child
from .daycare_models import DaycareSite, DaycareRoom
from .daycare_checkin_models import DaycareAttendance, DaycareRoomStaffCoverage


_ALLOWED_ROLES = ("DAYCARE_DIRECTOR", "DAYCARE_STAFF")
_CONFLICT_CODES = {
    "already_checked_in", "capacity_exceeded", "ratio_exceeded",
    "repeat_same_day_requires_review", "checkin_conflict",
    "attendance_not_open", "request_already_consumed", "release_conflict",
}
_NOT_FOUND_CODES = {"room_unavailable", "child_unavailable"}


class DaycareCheckinRequest(serializers.Serializer):
    site_id = serializers.UUIDField()
    room_id = serializers.UUIDField()
    child_id = serializers.UUIDField()
    program_code = serializers.ChoiceField(choices=["DAYCARE", "PRESCHOOL"])
    request_key = serializers.UUIDField()


class DaycareReleaseRequest(serializers.Serializer):
    site_id = serializers.UUIDField()
    room_id = serializers.UUIDField()
    attendance_id = serializers.UUIDField()
    guardian_authority_id = serializers.UUIDField()
    request_key = serializers.UUIDField()
    identity_verified = serializers.BooleanField()
    identity_method = serializers.ChoiceField(
        choices=["GOVERNMENT_PHOTO_ID", "APPROVED_PHOTO_ROSTER", "PERSONALLY_KNOWN"]
    )


def _strict_payload(request, serializer_cls):
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError({"detail": "Expected an object."})
    allowed = set(serializer_cls().fields)
    if set(data) - allowed:
        raise ValidationError({"detail": "Unexpected request fields."})
    serializer = serializer_cls(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _staff_scope(request, code, *, allow_inactive_school=False):
    """Never grant school-override rights to ordinary care staff.

    Restrict to the authenticated user's own canonical school, even when the
    platform middleware would permit a broader support role tenant override.
    Active-school enforcement is for admission only; custody release and
    custody roster reads must remain possible after a school is deactivated.
    """
    user = request.user
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        raise PermissionDenied("Authenticated active care staff required.")
    school_id = getattr(user, "school_id", None)
    if not isinstance(school_id, UUID) or not school_id.int:
        raise PermissionDenied("A school-bound staff identity is required.")
    for raw in (
        request.META.get("HTTP_X_SCHOOL_ID"),
        request.META.get("HTTP_X_CROWN_SCHOOL_ID"),
    ):
        if raw is None:
            continue
        try:
            supplied = UUID(str(raw).strip())
        except (ValueError, TypeError, AttributeError):
            raise NotFound() from None
        if supplied != school_id:
            raise NotFound()
    context = getattr(request, "crown_tenant", None)
    if context is not None and context.school_id is not None and context.school_id != school_id:
        raise NotFound()
    school = School.objects.filter(pk=school_id).first()
    if school is None or (not allow_inactive_school and not school.is_active):
        raise NotFound()
    if not user.roles.filter(school=school, role_code__in=_ALLOWED_ROLES).exists():
        raise PermissionDenied("Explicit Diadem staff role required.")
    if not user_has_permission(user, code, school=school):
        raise PermissionDenied("Diadem staff permission required.")
    return school


def _service_error(exc):
    code = exc.code
    http_status = (
        status.HTTP_409_CONFLICT if code in _CONFLICT_CODES
        else status.HTTP_404_NOT_FOUND if code in _NOT_FOUND_CODES
        else status.HTTP_400_BAD_REQUEST
    )
    return Response({"code": code, "detail": "Childcare action was not completed."}, status=http_status)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def daycare_checkin(request):
    school = _staff_scope(request, "diadem.daycare.checkin")
    payload = _strict_payload(request, DaycareCheckinRequest)
    try:
        record = checkin_child(
            school_id=school.id, actor_id=request.user.pk,
            site_id=payload["site_id"], room_id=payload["room_id"],
            child_id=payload["child_id"], program_code=payload["program_code"],
            request_key=payload["request_key"],
        )
    except CheckinRefused as exc:
        return _service_error(exc)
    return Response({
        "attendance_id": str(record.pk),
        "child_id": str(record.child_id),
        "site_id": str(record.site_id),
        "room_id": str(record.room_id),
        "care_date": record.care_date.isoformat(),
        "checked_in_at": record.checked_in_at.isoformat(),
        "status": "checked_in",
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def daycare_release(request):
    # Custody exit remains possible if the school or subscription is inactive.
    # This does not bypass the individual staff grant, approved guardian,
    # identity attestation, shift validation, audit or tenant boundary.
    school = _staff_scope(
        request, "diadem.daycare.release", allow_inactive_school=True
    )
    payload = _strict_payload(request, DaycareReleaseRequest)
    try:
        record = release_child(
            school_id=school.id, actor_id=request.user.pk,
            site_id=payload["site_id"], room_id=payload["room_id"],
            attendance_id=payload["attendance_id"],
            guardian_authority_id=payload["guardian_authority_id"],
            request_key=payload["request_key"],
            identity_verified=payload["identity_verified"],
            identity_method=payload["identity_method"],
        )
    except ReleaseRefused as exc:
        return _service_error(exc)
    return Response({
        "release_id": str(record.pk),
        "attendance_id": str(record.attendance_id),
        "child_id": str(record.child_id),
        "released_at": record.released_at.isoformat(),
        "status": "released",
    }, status=status.HTTP_201_CREATED)


def _visible_staff_room_ids(request, school, at):
    """Return read-authorized room IDs; None means an explicit director grant.

    Staff visibility follows *the same* verified, current assignment for site
    discovery and custody rosters. A conflicting active room assignment fails
    closed, including when only one shift is marked qualified. Never trust the
    selected site or a client-supplied staff ID to authorize an operation.
    """
    if request.user.roles.filter(
        school=school, role_code="DAYCARE_DIRECTOR"
    ).exists():
        return None

    qualified = DaycareRoomStaffCoverage.objects.filter(
        school=school, site__school=school, room__school=school,
        room__site_id=F("site_id"), staff=request.user,
        is_active=True, is_qualified=True, room__is_active=True,
        starts_at__lte=at, ends_at__gt=at,
        verified_at__isnull=False, verified_at__lte=at,
        verified_by__school=school, verified_by__is_active=True,
    ).exclude(qualification_evidence="")
    room_ids = set(qualified.values_list("room_id", flat=True))
    if not room_ids:
        raise PermissionDenied("Current verified room assignment required.")
    if len(room_ids) != 1:
        raise PermissionDenied("Simultaneous coverage of multiple rooms requires director review.")
    if DaycareRoomStaffCoverage.objects.filter(
        school=school, staff=request.user, is_active=True,
        starts_at__lte=at, ends_at__gt=at,
    ).exclude(room_id__in=room_ids).exists():
        raise PermissionDenied("Conflicting care-room assignments require director review.")
    return room_ids


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daycare_open_roster(request, site_id):
    """Return only school- and site-scoped children still awaiting release.

    No guardian custody details, clinical information, or other household
    members are disclosed in the operational roster response.
    """
    school = _staff_scope(
        request, "diadem.daycare.view", allow_inactive_school=True
    )
    site = DaycareSite.objects.filter(pk=site_id, school=school).first()
    if site is None:
        raise NotFound()
    now = timezone.now()
    room_ids = _visible_staff_room_ids(request, school, now)
    # A staff member on another site's shift cannot obtain an empty-but-valid
    # response for this site or probe which children are present there.
    if room_ids is not None and not DaycareRoom.objects.filter(
        school=school, site=site, pk__in=room_ids
    ).exists():
        raise PermissionDenied("Current verified site assignment required.")
    qs = DaycareAttendance.objects.filter(
        school=school, site=site, custody_release__isnull=True
    ).select_related("child", "room", "program").order_by("room__code", "child__last_name", "child__first_name", "pk")
    if room_ids is not None:
        qs = qs.filter(room_id__in=room_ids)
    rows = [{
        "attendance_id": str(row.pk),
        "child_id": str(row.child_id),
        "child_name": f"{row.child.first_name} {row.child.last_name}".strip(),
        "room_id": str(row.room_id),
        "room_name": row.room.name,
        "program_code": row.program.code,
        "care_date": row.care_date.isoformat(),
        "checked_in_at": row.checked_in_at.isoformat(),
    } for row in qs]
    return Response({
        "site_id": str(site.pk),
        "as_of": now.isoformat(),
        "children_present": len(rows),
        "rows": rows,
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daycare_sites(request):
    """Discover only school-owned centers with explicit Diadem view permission.

    On-duty staff see sites for their currently verified room coverage; a
    director may see all their school's sites, including inactive locations
    for pending custody reconciliation. This endpoint is read-only.
    """
    school = _staff_scope(
        request, "diadem.daycare.view", allow_inactive_school=True
    )
    room_ids = _visible_staff_room_ids(request, school, timezone.now())
    sites = DaycareSite.objects.filter(school=school)
    if not school.is_active:
        # An inactive school's directory exists only to locate unresolved
        # custody. Do not disclose empty/former centers, and never open
        # admissions, unrelated reads or general school functionality.
        open_custody_site_ids = DaycareAttendance.objects.filter(
            school=school, custody_release__isnull=True
        ).values("site_id")
        sites = sites.filter(pk__in=open_custody_site_ids)
    if room_ids is not None:
        sites = sites.filter(care_rooms__id__in=room_ids).distinct()
    return Response({"sites": [
        {"site_id": str(site.pk), "name": site.name, "is_active": site.is_active}
        for site in sites.order_by("name", "pk")
    ]})
