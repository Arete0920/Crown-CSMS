"""Read-only Admissions dashboard endpoints."""

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from admissions.models import AdmissionsApplication

from crown_api.dashboards.tenant import get_dashboard_school_id


class AdmissionsFunnelStageSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class AdmissionsFunnelDailySerializer(serializers.Serializer):
    day = serializers.DateField()
    count = serializers.IntegerField()


class AdmissionsFunnelDashboardResponseSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    by_stage = AdmissionsFunnelStageSerializer(many=True)
    daily_30d = AdmissionsFunnelDailySerializer(many=True)


class AdmissionsFunnelDashboard(APIView):
    """Admissions funnel: counts by status + 30-day creation trend."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Admissions"],
        responses=AdmissionsFunnelDashboardResponseSerializer,
    )
    def get(self, request):
        school_id = get_dashboard_school_id(request, required=True)

        now = timezone.now()
        start = now - timedelta(days=30)

        qs = AdmissionsApplication.objects.filter(school_id=school_id)

        by_stage = (
            qs.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        daily_30d = (
            qs.filter(created_at__gte=start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return Response(
            {
                "school_id": str(school_id),
                "by_stage": list(by_stage),
                "daily_30d": list(daily_30d),
            }
        )


# Back-compat with existing URL imports
AdmissionsFunnelView = AdmissionsFunnelDashboard
