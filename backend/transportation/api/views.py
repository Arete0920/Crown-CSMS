# backend/transportation/api/views.py
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from households.scoping import get_request_school_id
from transportation.models import Assignment, Driver, RideEvent, Route, Stop, StudentRider, Vehicle
from transportation.api.permissions import IsTransportationStaffOrReadOnly
from transportation.api.serializers import (
    AssignmentSerializer,
    DriverSerializer,
    RideEventSerializer,
    RouteSerializer,
    StopSerializer,
    StudentRiderSerializer,
    VehicleSerializer,
)


def _school_qs(qs, school_id):
    return qs.filter(school_id=school_id, is_deleted=False)


def _same_school(obj, school_id, field_name):
    if obj is not None and str(getattr(obj, "school_id", "")) != str(school_id):
        raise ValidationError({field_name: "Related object must belong to the requested school."})


class SchoolScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTransportationStaffOrReadOnly]
    school_relation_fields = ()

    def get_school_id(self):
        return get_request_school_id(self.request)

    def _validate_relations(self, serializer):
        school_id = self.get_school_id()
        for field_name in self.school_relation_fields:
            value = serializer.validated_data.get(field_name)
            if value is None and getattr(serializer, "instance", None) is not None:
                value = getattr(serializer.instance, field_name, None)
            _same_school(value, school_id, field_name)

    def perform_create(self, serializer):
        self._validate_relations(serializer)
        serializer.save(school_id=self.get_school_id())

    def perform_update(self, serializer):
        self._validate_relations(serializer)
        serializer.save()

    def get_queryset(self):  # pragma: no cover
        raise NotImplementedError


class VehicleViewSet(SchoolScopedViewSet):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return _school_qs(Vehicle.objects.order_by("name"), self.get_school_id()).order_by("name")

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])


class DriverViewSet(SchoolScopedViewSet):
    serializer_class = DriverSerializer

    def get_queryset(self):
        return _school_qs(Driver.objects.order_by("full_name"), self.get_school_id()).order_by("full_name")

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])


class RouteViewSet(SchoolScopedViewSet):
    serializer_class = RouteSerializer
    school_relation_fields = ("default_vehicle", "default_driver")

    def get_queryset(self):
        return (
            _school_qs(Route.objects.select_related("default_vehicle", "default_driver"), self.get_school_id())
            .prefetch_related("stops")
            .order_by("name")
        )

    @action(detail=True, methods=["get"], url_path="stops")
    def stops(self, request, pk=None):
        school_id = self.get_school_id()
        try:
            route = _school_qs(Route.objects.order_by("id"), school_id).get(pk=pk)
        except Route.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        stops = _school_qs(Stop.objects.filter(route=route), school_id).order_by("order", "id")
        return Response(StopSerializer(stops, many=True).data)


class StopViewSet(SchoolScopedViewSet):
    serializer_class = StopSerializer
    school_relation_fields = ("route",)

    def get_queryset(self):
        return _school_qs(Stop.objects.select_related("route").all(), self.get_school_id()).order_by(
            "route", "order", "id"
        )


class StudentRiderViewSet(SchoolScopedViewSet):
    serializer_class = StudentRiderSerializer
    school_relation_fields = ("pickup_stop", "dropoff_stop")

    def get_queryset(self):
        school_id = self.get_school_id()
        qs = _school_qs(StudentRider.objects.order_by("student_id"), school_id)
        school_year = self.request.query_params.get("school_year")
        if school_year:
            qs = qs.filter(school_year=school_year)
        route_id = self.request.query_params.get("route_id")
        if route_id:
            qs = qs.filter(pickup_stop__route_id=route_id) | qs.filter(dropoff_stop__route_id=route_id)
        return qs.order_by("student_id")


class AssignmentViewSet(SchoolScopedViewSet):
    serializer_class = AssignmentSerializer
    school_relation_fields = ("route", "driver", "vehicle")

    def get_queryset(self):
        return _school_qs(
            Assignment.objects.select_related("route", "driver", "vehicle"), self.get_school_id()
        ).order_by("-start_date")


class RideEventViewSet(SchoolScopedViewSet):
    serializer_class = RideEventSerializer
    school_relation_fields = ("route",)

    def get_queryset(self):
        qs = _school_qs(RideEvent.objects.select_related("route"), self.get_school_id())
        service_date = self.request.query_params.get("date")
        if service_date:
            qs = qs.filter(service_date=service_date)
        return qs.order_by("-service_date", "event_type")


class DispatchViewSet(viewsets.ViewSet):
    permission_classes = [IsTransportationStaffOrReadOnly]

    @action(detail=False, methods=["get"], url_path="run-sheet")
    def run_sheet(self, request):
        school_id = get_request_school_id(request)
        date_str = request.query_params.get("date")
        route_id = request.query_params.get("route_id")
        if not date_str or not route_id:
            return Response({"detail": "date and route_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            route = _school_qs(Route.objects.order_by("id"), school_id).get(pk=route_id)
        except Route.DoesNotExist:
            return Response({"detail": "Route not found."}, status=404)
        stops = _school_qs(Stop.objects.filter(route=route), school_id).order_by("order", "id")
        school_year = request.query_params.get("school_year", "")
        riders_qs = _school_qs(StudentRider.objects.order_by("student_id"), school_id)
        if school_year:
            riders_qs = riders_qs.filter(school_year=school_year)
        if route.direction == "AM":
            riders_qs = riders_qs.filter(pickup_stop__in=stops)
        else:
            riders_qs = riders_qs.filter(dropoff_stop__in=stops)
        return Response({
            "date": date_str,
            "route": {"id": str(route.id), "name": route.name, "direction": route.direction},
            "stops": StopSerializer(stops, many=True).data,
            "riders": StudentRiderSerializer(riders_qs, many=True).data,
        })
