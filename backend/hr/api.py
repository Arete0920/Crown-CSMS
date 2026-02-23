from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Employee
from .serializers import EmployeeSerializer


def _school_id(request):
    return request.headers.get("X-School-Id") or request.headers.get("X-School-ID")


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = _school_id(self.request)
        if not school_id:
            return Employee.objects.none()
        return Employee.objects.filter(school_id=school_id)

    def perform_create(self, serializer):
        school_id = _school_id(self.request)
        serializer.save(school_id=school_id)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hr_metrics(request):
    school_id = _school_id(request)
    if not school_id:
        return Response({"error": "X-School-Id required"}, status=400)
    qs = Employee.objects.filter(school_id=school_id)
    active = qs.filter(active=True)
    from django.db.models import Count
    by_dept = list(
        active.values("department")
        .annotate(count=Count("id"))
        .order_by("-count")
        .values("department", "count")
    )
    return Response({
        "total_employees": qs.count(),
        "active_employees": active.count(),
        "inactive_employees": qs.filter(active=False).count(),
        "by_department": by_dept,
    })
