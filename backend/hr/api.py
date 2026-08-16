from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Count

from core.audit import audit_event
from core.permissions import CrownModulePermission
from .models import Employee
from .serializers import EmployeeSerializer
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
    return school


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [CrownModulePermission("hr.view", write_code="hr.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return Employee.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("hr.employee.created", user=self.request.user, school=school,
                    extra={"employee_id": str(instance.id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        audit_event("hr.employee.updated", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"employee_id": str(instance.id)})

    def perform_destroy(self, instance):
        audit_event("hr.employee.deleted", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"employee_id": str(instance.id)})
        instance.delete()


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([CrownModulePermission("hr.view")])
def hr_metrics(request):
    school = _require_school(request)
    qs = Employee.objects.filter(school_id=school.id)
    active = qs.filter(active=True)
    by_dept = list(
        active.values("department").annotate(count=Count("id"))
        .order_by("-count").values("department", "count")
    )
    return Response({
        "total_employees":    qs.count(),
        "active_employees":   active.count(),
        "inactive_employees": qs.filter(active=False).count(),
        "by_department":      by_dept,
    })
