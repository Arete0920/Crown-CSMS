from rest_framework import serializers

from .models import AdmissionsApplication


class AdmissionsApplicationSerializer(serializers.ModelSerializer):
    """Read serializer for AdmissionsApplication. Used in registrar and admin views."""

    class Meta:
        model = AdmissionsApplication
        fields = [
            "id",
            "school_id",
            "academic_year_id",
            "family_id",
            "student_id",
            "household_id",
            "sis_student_id",
            "status",
            "submitted_at",
            "gpa",
            "test_score",
            "essay_received",
            "recommendations_received",
            "transcript_received",
            "notes_internal",
            "last_contacted_at",
            "last_contacted_by_id",
            "last_contacted_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AdmissionsApplicationWriteSerializer(serializers.ModelSerializer):
    """Write serializer for creating/updating AdmissionsApplication records."""

    class Meta:
        model = AdmissionsApplication
        fields = [
            "academic_year_id",
            "family_id",
            "student_id",
            "household_id",
            "sis_student_id",
            "status",
            "gpa",
            "test_score",
            "essay_received",
            "recommendations_received",
            "transcript_received",
            "notes_internal",
        ]
