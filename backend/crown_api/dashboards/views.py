from __future__ import annotations

import uuid as _uuid

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from crown_api.dashboards.models import DashboardSnapshot
from crown_api.dashboards.sample_payloads import (
    attendance_sample_payload,
    release_reliability_sample_payload,
)


def _request_user_is_authenticated(request):
    user = getattr(request, 'user', None)
    return bool(user and getattr(user, 'is_authenticated', False))


def _dev_open_api_enabled():
    return bool(getattr(settings, 'CROWN_DEV_OPEN_API', False))


def _allow_sample_dashboard_payloads():
    return bool(getattr(settings, 'CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS', False))


def _require_dashboard_authentication(request):
    if _request_user_is_authenticated(request):
        return
    if _dev_open_api_enabled():
        return
    raise PermissionDenied({'detail': 'Authentication credentials were not provided.'})


def _school_id_from_request(request):
    raw = request.headers.get('X-School-ID')
    if raw is None:
        user = getattr(request, 'user', None)
        user_school_id = getattr(user, 'school_id', None) if user else None
        raw = user_school_id or 'heritage-demo'
    value = str(raw).strip()
    return value or 'heritage-demo'


def _resolve_school_strict(
    request,
    *,
    require_user_school_binding=False,
    allow_dev_open_fallback=True,
):
    """Resolve an explicit X-School-Id tenant; dev-open may optionally use the configured demo school."""
    from core.models import School
    raw = request.META.get('HTTP_X_SCHOOL_ID', '').strip()
    if not raw:
        if allow_dev_open_fallback and _dev_open_api_enabled():
            demo_school_id = getattr(settings, 'CROWN_DEMO_SCHOOL_ID', None) or '11111111-1111-1111-1111-111111111111'
            school = School.objects.filter(pk=demo_school_id).first()
            if school is None:
                school = School.objects.create(id=_uuid.UUID(demo_school_id), name='Heritage Demo School')
            return school
        raise ValidationError({"detail": "X-School-Id header is required."})
    try:
        school_id = _uuid.UUID(raw)
    except (ValueError, AttributeError):
        raise ValidationError({"detail": "Invalid X-School-Id (must be a UUID)."})
    school = School.objects.filter(pk=school_id).first()
    if school is None:
        raise NotFound({"detail": "School not found."})
    # Cross-tenant check: non-staff users may only access their own school.
    # master-control additionally requires an explicit user-school binding.
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        user_school_id = getattr(user, 'school_id', None)
        if require_user_school_binding and not user_school_id:
            raise PermissionDenied({"detail": "Authenticated user is not assigned to a school."})
        if not getattr(user, 'is_staff', False) and user_school_id and str(user_school_id) != str(school.id):
            raise PermissionDenied({"detail": "Cross-tenant access denied."})
    return school


def _live_snapshot_or_none(*, school_id, dashboard_key):
    return DashboardSnapshot.objects.filter(
        school_id=str(school_id),
        dashboard_key=dashboard_key,
        source='live',
    ).order_by('-created_at').first()


def _snapshot_response(snapshot):
    payload = dict(snapshot.payload or {})
    meta = dict(payload.get('meta') or {})
    meta['served_from'] = 'live_db'
    meta['provenance'] = 'live_db'
    meta['live_certified'] = True
    meta['school_id'] = str(snapshot.school_id)
    payload['meta'] = meta
    return Response(payload)


def _unavailable_response(*, school_id, dashboard_key):
    return Response(
        {
            'detail': 'Live dashboard data is unavailable.',
            'code': 'dashboard_live_data_required',
            'dashboard_key': dashboard_key,
            'school_id': str(school_id),
            'meta': {
                'served_from': 'unavailable',
                'provenance': 'unavailable',
                'live_certified': False,
                'school_id': str(school_id),
            },
        },
        status=503,
    )


def _dashboard_payload_response(*, school_id, dashboard_key, sample_factory):
    snapshot = _live_snapshot_or_none(school_id=school_id, dashboard_key=dashboard_key)
    if snapshot is not None:
        return _snapshot_response(snapshot)

    if not _allow_sample_dashboard_payloads():
        return _unavailable_response(school_id=school_id, dashboard_key=dashboard_key)

    payload = sample_factory(str(school_id))
    meta = dict(payload.get('meta') or {})
    meta['served_from'] = 'sample'
    meta['provenance'] = 'sample'
    meta['live_certified'] = False
    meta['school_id'] = str(school_id)
    payload['meta'] = meta
    return Response(payload)


class AttendanceDashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_dashboard_authentication(request)
        school = _resolve_school_strict(request, allow_dev_open_fallback=False)
        return _dashboard_payload_response(
            school_id=school.id,
            dashboard_key='attendance',
            sample_factory=attendance_sample_payload,
        )


class ReleaseReliabilityDashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_dashboard_authentication(request)
        school = _resolve_school_strict(request, allow_dev_open_fallback=False)
        return _dashboard_payload_response(
            school_id=school.id,
            dashboard_key='release-reliability',
            sample_factory=release_reliability_sample_payload,
        )


class DashboardHealthView(APIView):
    permission_classes = []

    def get(self, request):
        return JsonResponse({'status': 'ok'})
