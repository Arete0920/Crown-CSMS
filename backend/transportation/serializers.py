from rest_framework import serializers
from .models import Vehicle, Driver, Route, Stop, StudentRider, Assignment, RideEvent


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id", "school", "vehicle_type", "name", "plate", "vin",
            "capacity", "notes", "insurance_expiry", "inspection_expiry",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id", "school", "full_name", "phone", "email",
            "is_contractor", "cdl_number", "cdl_expiry",
            "background_check_expiry", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = [
            "id", "school", "route", "order", "label", "address",
            "lat", "lon", "pickup_time", "dropoff_time",
            "safety_notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RouteSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            "id", "school", "name", "direction", "days_of_week",
            "active_start", "active_end", "default_vehicle", "default_driver",
            "notes", "created_at", "updated_at", "stops",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StudentRiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRider
        fields = [
            "id", "school", "student_id", "school_year", "is_eligible",
            "pickup_stop", "dropoff_stop", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "school", "route", "driver", "vehicle",
            "start_date", "end_date", "is_override", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = [
            "id", "school", "service_date", "route", "student_id",
            "event_type", "note", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

