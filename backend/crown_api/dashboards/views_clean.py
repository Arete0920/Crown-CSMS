"""
Clean dashboard endpoints that work with our custom JWT tokens
"""

import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from crown_api.jwt_utils import decode_access


logger = logging.getLogger(__name__)
INTERNAL_ERROR_DETAIL = "Internal server error"


def _get_bearer_token(request):
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get('Authorization', '') or request.META.get('HTTP_AUTHORIZATION', '')
    if auth.lower().startswith('bearer '):
        return auth.split(' ', 1)[1].strip()
    return None


def _authenticate_request(request):
    """Validate JWT and return decoded payload, or None if invalid."""
    token = _get_bearer_token(request)
    if not token:
        return None
    res = decode_access(token)
    if res.ok and res.payload:
        return res.payload
    return None


@csrf_exempt
@require_http_methods(["GET"])
def dashboard_me(request):
    """Return authenticated user's school context and roles."""
    try:
        # Manually validate JWT
        payload = _authenticate_request(request)
        if not payload:
            return JsonResponse({"detail": "Unauthorized"}, status=401)

        school_id_from_header = request.headers.get('X-School-Id')
        if not school_id_from_header:
            return JsonResponse({"detail": "X-School-Id header is required"}, status=400)

        return JsonResponse({
            "school_id": school_id_from_header,
            "roles": ["admin"],
            "default_route": "/director/",
            "features": [],
        })
    except Exception:
        logger.exception("dashboard_me failed")
        return JsonResponse({"detail": INTERNAL_ERROR_DETAIL}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def dashboard_summary(request):
    """Return dashboard summary widgets for the school."""
    try:
        # Manually validate JWT
        payload = _authenticate_request(request)
        if not payload:
            return JsonResponse({"detail": "Unauthorized"}, status=401)

        school_id_from_header = request.headers.get('X-School-Id')
        if not school_id_from_header:
            return JsonResponse({"detail": "X-School-Id header is required"}, status=400)

        # Return sample dashboard data
        return JsonResponse({
            "school_id": school_id_from_header,
            "widgets": [
                {"id": "admissions", "title": "Admissions", "count": 0},
                {"id": "billing", "title": "Billing", "count": 0},
                {"id": "attendance", "title": "Attendance", "count": 0},
            ]
        })
    except Exception:
        logger.exception("dashboard_summary failed")
        return JsonResponse({"detail": INTERNAL_ERROR_DETAIL}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def dashboard_drilldown(request):
    """Return drilldown data for a specific dashboard widget."""
    try:
        # Manually validate JWT
        payload = _authenticate_request(request)
        if not payload:
            return JsonResponse({"detail": "Unauthorized"}, status=401)

        school_id_from_header = request.headers.get('X-School-Id')
        widget = request.GET.get('widget', '')

        return JsonResponse({
            "widget": widget,
            "school_id": school_id_from_header,
            "rows": [],
            "page": 1,
        })
    except Exception:
        logger.exception("dashboard_drilldown failed")
        return JsonResponse({"detail": INTERNAL_ERROR_DETAIL}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def dashboard_alerts(request):
    """Return school-level alerts."""
    try:
        # Manually validate JWT
        payload = _authenticate_request(request)
        if not payload:
            return JsonResponse({"detail": "Unauthorized"}, status=401)

        school_id_from_header = request.headers.get('X-School-Id')

        return JsonResponse({
            "school_id": school_id_from_header,
            "alerts": []
        })
    except Exception:
        logger.exception("dashboard_alerts failed")
        return JsonResponse({"detail": INTERNAL_ERROR_DETAIL}, status=500)
