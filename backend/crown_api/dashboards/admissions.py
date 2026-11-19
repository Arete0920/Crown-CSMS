"""Read-only Admissions dashboard endpoints."""

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from admissions.models import AdmissionsApplication
from core.models import School
from core.permissions import user_has_permission

from crown_api.dashboards.tenant import get_dashboard_school_id


class AdmissionsFunnelDashboard(APIView):
    """Admissions funnel: counts by status + 30-day creation trend."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request, required=True)
        school = School.objects.filter(pk=school_id, is_active=True).first()
        if not user_has_permission(request.user, "admissions.view", school=school):
            raise PermissionDenied("Admissions access is not authorized.")

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
