from rest_framework import serializers
from .models import Application, Applicant, ApplicationEvent


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = [
            "id", "school_id", "application", "student",
            "first_name", "last_name", "grade_applying_for",
            "dob", "source", "flags", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationEvent
        fields = ["id", "school_id", "application", "event_type", "payload", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    applicants = ApplicantSerializer(many=True, read_only=True)
    events = ApplicationEventSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "school_id", "household", "status",
            "submitted_at", "decided_at", "created_at", "updated_at",
            "applicants", "events",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

