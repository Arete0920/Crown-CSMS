from rest_framework import serializers

from .models import AcademicYearWizardSession


class AcademicYearWizardSessionSerializer(serializers.ModelSerializer):
    """Read serializer for AcademicYearWizardSession — wizard state for year setup."""

    school_id = serializers.UUIDField(source="school.id", read_only=True)
    created_by_id = serializers.IntegerField(source="created_by.id", read_only=True, allow_null=True)

    class Meta:
        model = AcademicYearWizardSession
        fields = [
            "id",
            "school_id",
            "created_by_id",
            "year_name",
            "start_date",
            "end_date",
            "terms_config",
            "commit_result",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_by_id", "commit_result", "created_at", "updated_at"]


class AcademicYearWizardSessionWriteSerializer(serializers.ModelSerializer):
    """Write serializer for wizard step updates (configure and terms steps)."""

    class Meta:
        model = AcademicYearWizardSession
        fields = [
            "year_name",
            "start_date",
            "end_date",
            "terms_config",
        ]
