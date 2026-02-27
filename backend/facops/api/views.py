# backend/facops/api/views.py
from __future__ import annotations

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Crown canonical tenant helper
from households.scoping import get_request_school_id

from facops.models import (
    Alert,
    Asset,
    Drill,
    Location,
    SafetyIncident,
    VisitorLog,
    WorkOrder,
    WorkOrderComment,
)
from facops.api.permissions import (
    CanCreateWorkOrder,
    IsFacilitiesStaffOrReadOnly,
    IsSafetyOfficerOrReadOnly,
)
from facops.api.serializers import (
    AlertSerializer,
    AssetSerializer,
    DrillSerializer,
    LocationSerializer,
    SafetyIncidentSerializer,
    VisitorLogSerializer,
    WorkOrderCommentSerializer,
    WorkOrderSerializer,
)


class SchoolScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_school_id(self):
        return get_request_school_id(self.request)

    def perform_create(self, serializer):
        serializer.save(school=self._school())

    def _school(self):
        from core.models import School
        sid = self.get_school_id()
        return School.objects.get(id=sid)


class LocationViewSet(SchoolScopedViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsFacilitiesStaffOrReadOnly]

    def get_queryset(self):
        return (
            Location.objects
            .filter(school_id=self.get_school_id())
            .order_by("name")
        )

    def perform_create(self, serializer):
        serializer.save(school=self._school())


class AssetViewSet(SchoolScopedViewSet):
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated, IsFacilitiesStaffOrReadOnly]

    def get_queryset(self):
        return (
            Asset.objects
            .filter(school_id=self.get_school_id())
            .order_by("name")
        )

    def perform_create(self, serializer):
        serializer.save(school=self._school())


class WorkOrderViewSet(SchoolScopedViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated, CanCreateWorkOrder]

    def get_queryset(self):
        school_id = self.get_school_id()
        qs = (
            WorkOrder.objects
            .filter(school_id=school_id)
            .select_related("location", "asset", "requested_by", "assigned_to")
            .prefetch_related("comments")
        )
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        assigned_to = self.request.query_params.get("assigned_to")
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        school = self._school()
        serializer.save(school=school, requested_by=self.request.user)

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        school_id = self.get_school_id()
        try:
            wo = WorkOrder.objects.get(id=pk, school_id=school_id)
        except WorkOrder.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        new_status = request.data.get("status", "")
        if new_status not in dict(WorkOrder.STATUS_CHOICES):
            return Response({"detail": "invalid status"}, status=400)
        wo.status = new_status
        if new_status in (WorkOrder.STATUS_DONE, WorkOrder.STATUS_CANCELED):
            wo.closed_at = timezone.now()
        wo.save(update_fields=["status", "closed_at", "updated_at"])
        return Response(WorkOrderSerializer(wo).data)


class SafetyIncidentViewSet(SchoolScopedViewSet):
    serializer_class = SafetyIncidentSerializer
    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]

    def get_queryset(self):
        return (
            SafetyIncident.objects
            .filter(school_id=self.get_school_id())
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        school = self._school()
        serializer.save(school=school, reported_by=self.request.user)


class DrillViewSet(SchoolScopedViewSet):
    serializer_class = DrillSerializer
    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]

    def get_queryset(self):
        return (
            Drill.objects
            .filter(school_id=self.get_school_id())
            .order_by("-planned_for", "-created_at")
        )

    def perform_create(self, serializer):
        school = self._school()
        serializer.save(school=school, created_by=self.request.user)


class VisitorLogViewSet(SchoolScopedViewSet):
    serializer_class = VisitorLogSerializer
    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]

    def get_queryset(self):
        return (
            VisitorLog.objects
            .filter(school_id=self.get_school_id())
            .order_by("-checked_in_at")
        )

    def perform_create(self, serializer):
        serializer.save(school=self._school())


class AlertViewSet(SchoolScopedViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]

    def get_queryset(self):
        return (
            Alert.objects
            .filter(school_id=self.get_school_id())
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(school=self._school(), emitted_by=self.request.user)

    @action(detail=False, methods=["post"])
    def emit(self, request):
        title = request.data.get("title", "").strip()
        body = request.data.get("body", "").strip()
        channel = request.data.get("channel", "TEAMS")
        if not title:
            return Response({"detail": "title required"}, status=400)
        school = self._school()
        alert = Alert.objects.create(
            school=school,
            title=title,
            body=body,
            channel=channel,
            emitted_by=request.user,
        )
        return Response(AlertSerializer(alert).data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def facilities_summary(request):
    school_id = get_request_school_id(request)
    closed_statuses = [WorkOrder.STATUS_DONE, WorkOrder.STATUS_CANCELED]
    total_open = (
        WorkOrder.objects
        .filter(school_id=school_id)
        .exclude(status__in=closed_statuses)
        .count()
    )
    by_status = list(
        WorkOrder.objects
        .filter(school_id=school_id)
        .values("status")
        .order_by("status")
    )
    return Response({
        "total_open_work_orders": total_open,
        "by_status": by_status,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def security_summary(request):
    school_id = get_request_school_id(request)
    total_incidents = SafetyIncident.objects.filter(school_id=school_id).count()
    open_incidents = SafetyIncident.objects.filter(
        school_id=school_id, resolved_at__isnull=True
    ).count()
    drills_total = Drill.objects.filter(school_id=school_id).count()
    drills_completed = Drill.objects.filter(
        school_id=school_id, completed_at__isnull=False
    ).count()
    from django.utils import timezone
    today = timezone.localdate()
    visitors_today = VisitorLog.objects.filter(
        school_id=school_id,
        checked_in_at__date=today,
    ).count()
    return Response({
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "drills_total": drills_total,
        "drills_completed": drills_completed,
        "visitors_today": visitors_today,
    })
