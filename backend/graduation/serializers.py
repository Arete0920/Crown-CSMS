from rest_framework import serializers
from .models import GraduationRule


class GraduationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraduationRule
        fields = [
            "id", "school", "name", "required_total_credits",
            "min_gpa", "is_active", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

