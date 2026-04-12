from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.models import School
from core.scoping import resolve_role
from crown_api.executive360.permissions import EXECUTIVE_ALLOWED_ROLES
from crown_api.executive360.serializers import (
    DrilldownSerializer,
    ExecutiveOverviewSerializer,
    GhostModeSerializer,
)
from crown_api.executive360.services import (
    ExecutiveContext,
    build_executive_overview,
    get_chart_drilldown,
    get_ghost_mode_context,
    get_kpi_drilldown,
)


logger = logging.getLogger(__name__)


def _get_school(request):
    school = getattr(request, "school", None) or getattr(getattr(request, "user", None), "school", None)
    if school:
        return school

    sid = request.headers.get("X-School-Id")
    if not sid:
        return None

    try:
        return School.objects.get(pk=sid)
    except School.DoesNotExist:
        return None


class ExecutiveBaseView(GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def _guard_request(self, request):
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response(
                {"detail": "Missing or invalid school context"},
                status=status.HTTP_400_BAD_REQUEST,
            ), None

        school = _get_school(request)
        if school is None:
            return Response(
                {"detail": "Missing or invalid school context"},
                status=status.HTTP_400_BAD_REQUEST,
            ), None

        school_id = getattr(school, "id", None)
        role = resolve_role(user, school_id=school_id)
        if role not in EXECUTIVE_ALLOWED_ROLES:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN), None

        user_school_id = getattr(user, "school_id", None) or getattr(getattr(user, "school", None), "id", None)
        if user_school_id and school_id and str(user_school_id) != str(school_id):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND), None

        context = ExecutiveContext(
            user=user,
            school=school,
            ghost_mode=get_ghost_mode_context(request),
        )
        return None, context


class ExecutiveSelfOverview(ExecutiveBaseView):
    """GET /api/executive360/me/overview/"""

    serializer_class = ExecutiveOverviewSerializer

    @extend_schema(tags=["executive360"], responses=ExecutiveOverviewSerializer)
    def get(self, request):
        denied, context = self._guard_request(request)
        if denied is not None:
            return denied

        payload = build_executive_overview(context)
        serializer = self.get_serializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExecutiveKpiDrilldownView(ExecutiveBaseView):
    serializer_class = DrilldownSerializer

    @extend_schema(tags=["executive360"], responses=DrilldownSerializer)
    def get(self, request, kpi_key: str):
        denied, context = self._guard_request(request)
        if denied is not None:
            return denied

        payload = get_kpi_drilldown(context, kpi_key)
        serializer = self.get_serializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExecutiveChartDrilldownView(ExecutiveBaseView):
    serializer_class = DrilldownSerializer

    @extend_schema(tags=["executive360"], responses=DrilldownSerializer)
    def get(self, request, chart_key: str):
        denied, context = self._guard_request(request)
        if denied is not None:
            return denied

        payload = get_chart_drilldown(context, chart_key)
        serializer = self.get_serializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExecutiveGhostContextView(ExecutiveBaseView):
    serializer_class = GhostModeSerializer

    @extend_schema(tags=["executive360"], responses=GhostModeSerializer)
    def get(self, request):
        denied, context = self._guard_request(request)
        if denied is not None:
            return denied

        serializer = self.get_serializer(context.ghost_mode)
        return Response(serializer.data, status=status.HTTP_200_OK)
