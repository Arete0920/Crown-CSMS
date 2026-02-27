# backend/transportation/api/serializers.py
from rest_framework import serializers

from transportation.models import (
    Assignment,
    Driver,
    RideEvent,
    Route,
    Stop,
    StudentRider,
    Vehicle,
)


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


class StudentRiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRider
        fields = [
            "id", "student_id", "school_year", "is_eligible",
            "pickup_stop", "dropoff_stop", "notes",
            "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "route", "driver", "vehicle",
            "start_date", "end_date", "is_override",
            "notes", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = [
            "id", "service_date", "route", "student_id",
            "event_type", "note", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
