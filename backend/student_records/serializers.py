from rest_framework import serializers

from core.models import Student


class StudentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "school_id",
            "student_number",
            "first_name",
            "last_name",
            "dob",
            "status",
            "current_grade_level_id",
            "family_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
