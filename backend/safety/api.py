from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count

from .models import IncidentReport
from .serializers import IncidentSerializer


def _school_id(request):
    return request.headers.get("X-School-Id") or request.headers.get("X-School-ID")


class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = _school_id(self.request)
        if not school_id:
            return IncidentReport.objects.none()
        return IncidentReport.objects.filter(school_id=school_id)

    def perform_create(self, serializer):
        serializer.save(school_id=_school_id(self.request))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def safety_metrics(request):
    school_id = _school_id(request)
    if not school_id:
        return Response({"error": "X-School-Id required"}, status=400)

    qs = IncidentReport.objects.filter(school_id=school_id)
    open_qs = qs.filter(resolved=False)

    by_severity = list(
        open_qs.values("severity").annotate(count=Count("id")).order_by("-count").values("severity", "count")
    )
    by_category = list(
        qs.values("category").annotate(count=Count("id")).order_by("-count")[:5].values("category", "count")
    )

    return Response({
        "total_incidents": qs.count(),
        "open_incidents": open_qs.count(),
        "resolved_incidents": qs.filter(resolved=True).count(),
        "critical_open": open_qs.filter(severity="critical").count(),
        "by_severity": by_severity,
        "by_category": by_category,
    })
