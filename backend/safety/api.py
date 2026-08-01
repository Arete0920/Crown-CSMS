from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count

from core.audit import audit_event
from core.permissions import CrownModulePermission
from .models import IncidentReport
from .serializers import IncidentSerializer as IncidentReportSerializer
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
    return school


class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentReportSerializer
    permission_classes = [CrownModulePermission("safety.view", write_code="safety.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return IncidentReport.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("safety.incident.created", user=self.request.user, school=school,
                    extra={"incident_id": str(instance.id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        audit_event("safety.incident.updated", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"incident_id": str(instance.id)})

    def perform_destroy(self, instance):
        audit_event("safety.incident.deleted", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"incident_id": str(instance.id)})
        instance.delete()


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def safety_metrics(request):
    school = _require_school(request)
    qs = IncidentReport.objects.filter(school_id=school.id)
    by_severity = list(
        qs.values("severity").annotate(count=Count("id"))
        .order_by("severity").values("severity", "count")
    )
    total_incidents = qs.count()
    open_incidents = qs.filter(resolved=False).count()
    closed_incidents = qs.filter(resolved=True).count()
    by_status = [
        {"status": "open", "count": open_incidents},
        {"status": "closed", "count": closed_incidents},
    ]
    return Response({
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "closed_incidents": closed_incidents,
        "by_severity": by_severity,
        "by_status": by_status,
    })
