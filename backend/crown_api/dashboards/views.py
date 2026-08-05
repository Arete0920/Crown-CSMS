from copy import deepcopy
import os

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class DevOpenApiPermissions:
    """Allow local/dev access when the project explicitly enables it."""

    @staticmethod
    def has_permission(request, view):
        if _dev_open_api_enabled():
            return True
        return IsAuthenticated().has_permission(request, view)


from core.permissions import user_has_permission
from sandbox_demo.catalog import DEMO_SCHOOL_ID, SANDBOX_PERSONAS

from .live_personas import (
    LIVE_PERSONA_DASHBOARDS,
    PersonaDashboardPermissionDenied,
    build_persona_dashboard_payload,
)
from .models import DashboardSnapshot
from .payload_contract import validate_dashboard_payload
from .sample_payloads import SAMPLE_PAYLOAD_BUILDERS
from .batch5_extra_payloads import BATCH5_EXTRA_PAYLOAD_BUILDERS
import uuid as _uuid


DASHBOARD_PAYLOAD_BUILDERS = {
    **SAMPLE_PAYLOAD_BUILDERS,
    **BATCH5_EXTRA_PAYLOAD_BUILDERS,
}

# These builders query authoritative runtime services and self-identify as
# live/live_db only when that query succeeds. Production may execute them, but
# it must still reject any sample fallback they return.
LIVE_RUNTIME_DASHBOARDS = frozenset({
    'school-board',
})

STAFF_ONLY_DASHBOARDS = frozenset({
    'dashboard-certification-center',
})

STRICT_TENANT_DASHBOARDS = frozenset({
    'athletics-director',
    'compliance-audit',
    'data-migration',
    'extended-care',
    'implementation-success',
    'integrations-automation',
    'master-control',
    'revenue-operations',
    'summer-camp',
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def _is_production_runtime() -> bool:
    env = (
        str(getattr(settings, 'CROWN_ENV', '') or '')
        or str(getattr(settings, 'DJANGO_ENV', '') or '')
        or str(getattr(settings, 'ENVIRONMENT', '') or '')
        or str(os.getenv('CROWN_ENV', '') or '')
        or str(os.getenv('DJANGO_ENV', '') or '')
        or str(os.getenv('ENVIRONMENT', '') or '')
        or str(os.getenv('AZURE_ENVIRONMENT', '') or '')
    ).strip().lower()
    return env in {'prod', 'production', 'live'} or bool(os.getenv('WEBSITE_HOSTNAME'))


def _dev_open_api_enabled() -> bool:
    # Never allow dev-open bypass in production-like runtimes.
    return bool(getattr(settings, 'CROWN_DEV_OPEN_API', False)) and not _is_production_runtime()


def _sample_dashboard_payloads_allowed(request=None) -> bool:
    """
    Allow sample dashboard payloads when explicitly enabled, in clearly
    non-production runtimes, or for an authenticated Heritage sandbox session
    whose requested persona matches an assigned user role.

    Production tenants outside the bounded Heritage sandbox exception remain
    live/snapshot-only.
    """
    if _env_flag('CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS', default=False):
        return True

    user = getattr(request, 'user', None) if request is not None else None
    demo_role = str(request.headers.get('X-Demo-Role', '') or '').strip() if request is not None else ''
    request_school_id = str(request.headers.get('X-School-ID', '') or '').strip() if request is not None else ''
    user_school_id = str(getattr(user, 'school_id', '') or '').strip() if user is not None else ''
    persona = SANDBOX_PERSONAS.get(demo_role)
    role_matches = bool(
        persona
        and user
        and getattr(user, 'is_authenticated', False)
        and user.roles.filter(
            school_id=DEMO_SCHOOL_ID,
            role_code=persona.role_code,
        ).exists()
    )
    if (
        role_matches
        and request_school_id == str(DEMO_SCHOOL_ID)
        and user_school_id == str(DEMO_SCHOOL_ID)
    ):
        return True

    if bool(getattr(settings, 'CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS', False)):
        return True

    if _is_production_runtime():
        return False

    return True


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
    """Resolve X-School-Id; an optional dev-open fallback may use the configured demo school."""
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
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        if not getattr(user, 'is_staff', False) and not getattr(user, 'is_superuser', False):
            user_school_id = getattr(user, 'school_id', None)
            if require_user_school_binding and not user_school_id:
                raise NotFound({"detail": "Not found."})
            if user_school_id and str(user_school_id) != str(school_id):
                raise NotFound({"detail": "Not found."})
    return school


def _live_meta(*, school_id, source):
    return {
        'served_from': 'live',
        'source': source,
        'school_id': str(school_id),
    }


def _build_verified_live_payload(key, school_id):
    if key not in LIVE_RUNTIME_DASHBOARDS:
        return None

    payload = deepcopy(DASHBOARD_PAYLOAD_BUILDERS[key](school_id))
    payload.setdefault('meta', {})
    payload['meta']['school_id'] = school_id
    served_from = str(payload['meta'].get('served_from') or '').strip().lower()
    if served_from not in {'live', 'live_db'}:
        return None

    validate_dashboard_payload(payload)
    return payload


@api_view(['GET'])
@permission_classes([DevOpenApiPermissions])
def dashboard_me(request):
    """Return the current school context and roles for the requesting user."""
    school = _resolve_school_strict(request)
    from core.models import UserRole

    user = getattr(request, 'user', None)
    roles = []
    if user and getattr(user, 'is_authenticated', False):
        roles = list(
            UserRole.objects.filter(user=user, school=school).values_list('role_code', flat=True)
        )
        if not roles:
            user_school_id = getattr(user, 'school_id', None)
            if user_school_id and str(user_school_id) == str(school.id):
                roles = ['SCHOOL_MEMBER']

    return Response({
        "school_id": str(school.id),
        "roles": roles,
        "default_route": "/director/",
        "features": [],
        "meta": _live_meta(school_id=school.id, source='core_identity'),
    })


@api_view(['GET'])
@permission_classes([DevOpenApiPermissions])
def dashboard_summary(request):
    """Return dashboard summary widgets for the school."""
    school = _resolve_school_strict(request)
    widgets = [
        {
            "key": "quick_actions",
            "type": "quick_actions",
            "title": "Quick Actions",
            "size": "sm",
            "priority": 1,
            "data": {},
        }
    ]
    return Response({
        "school_id": str(school.id),
        "widgets": widgets,
        "meta": _live_meta(school_id=school.id, source='dashboard_service'),
    })


@api_view(['GET'])
@permission_classes([DevOpenApiPermissions])
def dashboard_drilldown(request):
    """Return drilldown data for a specific dashboard widget."""
    school = _resolve_school_strict(request)
    widget = request.query_params.get('widget', '').strip()
    if not widget:
        return Response({"detail": "widget parameter is required."}, status=400)
    return Response({
        "widget": widget,
        "school_id": str(school.id),
        "rows": [],
        "page": 1,
        "meta": _live_meta(school_id=school.id, source='dashboard_service'),
    })


@api_view(['GET'])
@permission_classes([DevOpenApiPermissions])
def dashboard_alerts(request):
    """Return school-level alerts."""
    school = _resolve_school_strict(request)
    return Response({
        "alerts": [],
        "meta": _live_meta(school_id=school.id, source='dashboard_service'),
    })


class DashboardSummaryView(APIView):
    permission_classes = [DevOpenApiPermissions]

    def get(self, request, dashboard_key):
        key = str(dashboard_key).strip().lower()
        user = getattr(request, 'user', None)

        if not user or not getattr(user, 'is_authenticated', False):
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        school_id = _school_id_from_request(request)

        if key in STAFF_ONLY_DASHBOARDS:
            if not getattr(user, 'is_staff', False) and not getattr(user, 'is_superuser', False):
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        if key == 'portrait-service':
            school = _resolve_school_strict(request, allow_dev_open_fallback=False)
            if not user_has_permission(user, 'spiritual_life.view', school=school):
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
            school_id = str(school.id)

        if key in STRICT_TENANT_DASHBOARDS:
            school = _resolve_school_strict(
                request,
                require_user_school_binding=(key == 'master-control'),
                allow_dev_open_fallback=False,
            )
            school_id = str(school.id)

        if key not in DASHBOARD_PAYLOAD_BUILDERS and key not in LIVE_PERSONA_DASHBOARDS:
            return Response(
                {
                    'code': 'unknown_dashboard',
                    'message': f'No dashboard payload contract registered for "{key}".',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if key in LIVE_PERSONA_DASHBOARDS:
            school = _resolve_school_strict(request, allow_dev_open_fallback=False)
            try:
                payload = build_persona_dashboard_payload(
                    dashboard_key=key,
                    user=user,
                    school=school,
                )
            except PersonaDashboardPermissionDenied:
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
            validate_dashboard_payload(payload)
            return Response(payload, status=status.HTTP_200_OK)

        if key in LIVE_RUNTIME_DASHBOARDS:
            school = _resolve_school_strict(request, allow_dev_open_fallback=False)
            school_id = str(school.id)

        live_payload = _build_verified_live_payload(key, school_id)
        if live_payload is not None:
            return Response(live_payload, status=status.HTTP_200_OK)

        snapshot = DashboardSnapshot.objects.filter(
            school_id=school_id,
            dashboard_key=key,
        ).first()

        if snapshot:
            payload = deepcopy(snapshot.payload or {})
            payload.setdefault('meta', {})
            payload['meta']['served_from'] = 'snapshot'
            payload['meta']['snapshot_updated_at'] = snapshot.updated_at.isoformat()
            payload['meta']['snapshot_source'] = snapshot.source
            payload['meta']['school_id'] = school_id
            validate_dashboard_payload(payload)
            return Response(payload, status=status.HTTP_200_OK)

        if not _sample_dashboard_payloads_allowed(request):
            return Response(
                {
                    'code': 'dashboard_live_data_required',
                    'message': f'No live or snapshot payload is available for "{key}" in this environment.',
                    'dashboard_key': key,
                    'school_id': school_id,
                    'required_resolution': 'Create a live dashboard service or certified DashboardSnapshot before production/full-completion certification.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = DASHBOARD_PAYLOAD_BUILDERS[key](school_id)
        payload = deepcopy(payload)
        payload.setdefault('meta', {})
        payload['meta'].setdefault('served_from', 'sample')
        payload['meta']['school_id'] = school_id
        payload['meta']['sample_payload_allowed'] = True
        validate_dashboard_payload(payload)
        return Response(payload, status=status.HTTP_200_OK)
