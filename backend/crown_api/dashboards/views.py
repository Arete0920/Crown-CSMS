"""
Dashboard API views — Me / Summary / Drilldown / Alerts.

Tenant safety: every request goes through get_dashboard_school_id()
which validates the X-School-Id header, enforces UUID format, and
cross-checks against the authenticated user's school.

RBAC: role is resolved from request.user.role first; falls back to
X-Demo-Role header only when ALLOW_DEMO_ROLE_HEADER=1 (dev/CI only).
"""
from __future__ import annotations

import logging
import os

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from crown_api.dashboards.tenant import get_dashboard_school_id
from crown_api.dashboards.serializers import (
    DashboardMeSerializer,
    DashboardSummarySerializer,
    DashboardAlertsResponseSerializer,
)
from crown_api.dashboards.summary import (
    build_dashboard_summary,
    build_dashboard_alerts,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_ROLES = frozenset({
    "admin", "teacher", "parent", "student",
    "finance", "registrar", "staff", "board",
})


def _resolve_role(request) -> str:
    """Resolve role from user model, then demo header (only in dev mode)."""
    user = getattr(request, "user", None)
    user_role = getattr(user, "role", None)
    if user_role:
        r = str(user_role).strip().lower()
        if r in _VALID_ROLES:
            return r

    if os.getenv("ALLOW_DEMO_ROLE_HEADER") == "1":
        hdr = None
        try:
            hdr = request.headers.get("X-Demo-Role") or request.META.get("HTTP_X_DEMO_ROLE")
        except Exception:
            logger.debug("role header resolution failed", exc_info=True)
        if hdr:
            r = str(hdr).strip().lower()
            if r in _VALID_ROLES:
                return r

    return "admin"  # safe default


def _resolve_display_name(request) -> str:
    user = getattr(request, "user", None)
    if user:
        return (
            getattr(user, "get_full_name", lambda: "")()
            or getattr(user, "email", "")
            or getattr(user, "username", "User")
        )
    return "User"


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class DashboardMeView(APIView):
    """
    GET /api/dashboards/me/
    Returns school context, resolved role(s), and default route for this user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request)  # raises 400/404 on bad input
        role = _resolve_role(request)
        payload = {
            "school_id": str(school_id),
            "display_name": _resolve_display_name(request),
            "roles": [role],
            "default_route": f"/dash/{role}",
            "features": {"flip_cards": True, "drilldowns": True},
        }
        ser = DashboardMeSerializer(payload)
        return Response(ser.data)


class DashboardSummaryView(APIView):
    """
    GET /api/dashboards/summary/
    Returns widget layout + summary metrics for the current user's role.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request)
        role = _resolve_role(request)
        data = build_dashboard_summary(role=role, school_id=str(school_id))
        ser = DashboardSummarySerializer(data=data)
        ser.is_valid(raise_exception=True)
        return Response(ser.data, status=status.HTTP_200_OK)


class DashboardDrilldownView(APIView):
    """
    GET /api/dashboards/drilldown/?widget=<key>
    Returns detailed rows for a given widget (paginated, Phase A returns stub).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request)
        widget_key = request.query_params.get("widget", "")
        if not widget_key:
            return Response(
                {"detail": "Missing required query parameter: widget"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Phase A: echo widget key + school; Phase B: real paginated queries per key
        return Response({
            "widget": widget_key,
            "school_id": str(school_id),
            "page": 1,
            "has_more": False,
            "rows": [],
            "meta": {"phase": "A", "note": "Drilldown rows coming in Phase B"},
        })


class DashboardAlertsView(APIView):
    """
    GET /api/dashboards/alerts/
    Returns actionable alert items for the current school.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import datetime, timezone
        school_id = get_dashboard_school_id(request)
        alerts = build_dashboard_alerts(str(school_id))
        payload = {
            "school_id": str(school_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "alerts": alerts,
        }
        ser = DashboardAlertsResponseSerializer(data=payload)
        ser.is_valid(raise_exception=True)
        return Response(ser.data)
