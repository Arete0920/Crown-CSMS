"""
analytics/api_health.py

Stage 5 customer health + export API endpoints:

  GET  /api/v1/analytics/health/              — school health score
  POST /api/v1/analytics/export/              — trigger school data export download
  GET  /api/v1/status/                        — public uptime/status page data
"""
import logging

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id
from analytics.services_health import upsert_customer_health
from core.services.export_service import export_school_data

logger = logging.getLogger("crown.analytics")


@extend_schema(tags=["Analytics"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_health(request):
    """Return the current health score for the caller's school."""
    school_id = get_request_school_id(request)
    record = upsert_customer_health(school_id)
    return Response({
        "school_id": str(school_id),
        "login_frequency_score": record.login_frequency_score,
        "payment_failure_score": record.payment_failure_score,
        "support_ticket_score": record.support_ticket_score,
        "overall_score": record.overall_score,
        "computed_at": record.computed_at,
    })


@extend_schema(tags=["Analytics"], request=OpenApiTypes.OBJECT, responses={(200, "application/zip"): OpenApiTypes.BINARY, 500: OpenApiTypes.OBJECT})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def export_school(request):
    """
    Trigger school data export and stream it as a ZIP download.
    This is a synchronous endpoint for small schools. Wire to Celery for large datasets.
    """
    school_id = get_request_school_id(request)
    try:
        buffer = export_school_data(school_id)
    except Exception as exc:
        logger.exception("Export failed for school_id=%s: %s", school_id, exc)
        return Response({"detail": "Export failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response = HttpResponse(buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = f"attachment; filename=crown_school_{school_id}_export.zip"
    return response


@extend_schema(tags=["Analytics"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_status(request):
    """Public platform status page — no auth required."""
    return Response({
        "status": "operational",
        "uptime_percent": "99.95",
        "last_incident": None,
        "components": {
            "api": "operational",
            "database": "operational",
            "celery": "operational",
            "storage": "operational",
        },
    })
