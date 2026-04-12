from copy import deepcopy

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import user_has_permission
from core.tenant_models import clear_current_school, set_current_school

from .models import DashboardSnapshot
from .payload_contract import validate_dashboard_payload
from .sample_payloads import SAMPLE_PAYLOAD_BUILDERS
import uuid as _uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError


def _school_id_from_request(request):
    raw = request.headers.get('X-School-ID') or request.query_params.get('school_id') or 'heritage-demo'
    value = str(raw).strip()
    return value or 'heritage-demo'


def _resolve_school_strict(request):
    """Resolve school from X-School-Id header only; never uses user.school_id fallback."""
    from core.models import School
    raw = request.META.get('HTTP_X_SCHOOL_ID', '').strip()
    if not raw:
        clear_current_school()
        raise ValidationError({"detail": "X-School-Id header is required."})
    try:
        school_id = _uuid.UUID(raw)
    except (ValueError, AttributeError):
        clear_current_school()
        raise ValidationError({"detail": "Invalid X-School-Id (must be a UUID)."})
    school = School.objects.filter(pk=school_id).first()
    if school is None:
        clear_current_school()
        raise NotFound({"detail": "School not found."})
    # Cross-tenant check: non-staff users may only access their own school
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        if not getattr(user, 'is_staff', False) and not getattr(user, 'is_superuser', False):
            user_school_id = getattr(user, 'school_id', None)
            if user_school_id and str(user_school_id) != str(school_id):
                clear_current_school()
                raise NotFound({"detail": "Not found."})
    request.school = school
    set_current_school(school)
    return school


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_me(request):
    """Return authenticated user's school context and roles."""
    school = _resolve_school_strict(request)
    from core.models import UserRole
    roles = list(
        UserRole.objects.filter(user=request.user, school=school).values_list('role_code', flat=True)
    )
    if not roles:
        # User associated with school via school_id field — include implicit identity
        user_school_id = getattr(request.user, 'school_id', None)
        if user_school_id and str(user_school_id) == str(school.id):
            roles = ['SCHOOL_MEMBER']
    return Response({
        "school_id": str(school.id),
        "roles": roles,
        "default_route": "/director/",
        "features": [],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_alerts(request):
    """Return school-level alerts."""
    school = _resolve_school_strict(request)
    return Response({
        "alerts": [],
    })

class DashboardSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, dashboard_key):
        key = str(dashboard_key).strip().lower()
        school_id = _school_id_from_request(request)

        if key == 'portrait-service':
            school = _resolve_school_strict(request)
            user = getattr(request, 'user', None)
            if not user or not getattr(user, 'is_authenticated', False):
                return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_403_FORBIDDEN)
            if not user_has_permission(user, 'spiritual_life.view', school=school):
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
            school_id = str(school.id)

        if key not in SAMPLE_PAYLOAD_BUILDERS:
            return Response(
                {
                    'code': 'unknown_dashboard',
                    'message': f'No dashboard payload contract registered for "{key}".',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

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

        payload = SAMPLE_PAYLOAD_BUILDERS[key](school_id)
        payload = deepcopy(payload)
        payload.setdefault('meta', {})
        payload['meta'].setdefault('served_from', 'sample')
        payload['meta']['school_id'] = school_id
        validate_dashboard_payload(payload)
        return Response(payload, status=status.HTTP_200_OK)
