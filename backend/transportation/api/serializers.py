from rest_framework import serializers

from households.scoping import get_request_school_id
from transportation.models import (
    Assignment,
    Driver,
    RideEvent,
    Route,
    Stop,
    StudentRider,
    Vehicle,
)


def _request_school_id(serializer):
    request = serializer.context.get("request")
    if request is None:
        return None
    return get_request_school_id(request, required=True)


def _same_school(serializer, field_name, value):
    if value is None:
        return value
    school_id = _request_school_id(serializer)
    if school_id is not None and str(value.school_id) != str(school_id):
        raise serializers.ValidationError(
            {field_name: "Related object does not belong to the active school."}
        )
    return value


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id", "vehicle_type", "name", "plate", "vin", "capacity",
            "notes", "insurance_expiry", "inspection_expiry",
            "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id", "full_name", "phone", "email", "is_contractor",
            "cdl_number", "cdl_expiry", "background_check_expiry",
            "notes", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = [
            "id", "route", "order", "label", "address",
            "lat", "lon", "pickup_time", "dropoff_time", "safety_notes",
        ]
        read_only_fields = ["id"]

    def validate_route(self, value):
        return _same_school(self, "route", value)


class RouteSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            "id", "name", "direction", "days_of_week",
            "active_start", "active_end",
            "default_vehicle", "default_driver",
            "notes", "stops", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_default_vehicle(self, value):
        return _same_school(self, "default_vehicle", value)

    def validate_default_driver(self, value):
        return _same_school(self, "default_driver", value)


class StudentRiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRider
        fields = [
            "id", "student_id", "school_year", "is_eligible",
            "pickup_stop", "dropoff_stop", "notes",
            "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_pickup_stop(self, value):
        return _same_school(self, "pickup_stop", value)

    def validate_dropoff_stop(self, value):
        return _same_school(self, "dropoff_stop", value)


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "route", "driver", "vehicle",
            "start_date", "end_date", "is_override",
            "notes", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_route(self, value):
        return _same_school(self, "route", value)

    def validate_driver(self, value):
        return _same_school(self, "driver", value)

    def validate_vehicle(self, value):
        return _same_school(self, "vehicle", value)


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = [
            "id", "service_date", "route", "student_id",
            "event_type", "note", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_route(self, value):
        return _same_school(self, "route", value)
