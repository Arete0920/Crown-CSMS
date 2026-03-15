from copy import deepcopy

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DashboardSnapshot
from .payload_contract import validate_dashboard_payload
from .sample_payloads import SAMPLE_PAYLOAD_BUILDERS


def _school_id_from_request(request):
    raw = request.headers.get('X-School-ID') or request.query_params.get('school_id') or 'heritage-demo'
    value = str(raw).strip()
    return value or 'heritage-demo'


class DashboardSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, dashboard_key):
        key = str(dashboard_key).strip().lower()
        school_id = _school_id_from_request(request)

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
        payload['meta']['served_from'] = 'sample'
        payload['meta']['school_id'] = school_id
        validate_dashboard_payload(payload)
        return Response(payload, status=status.HTTP_200_OK)
