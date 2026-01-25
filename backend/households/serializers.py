from rest_framework import serializers
from .models import Guardian, Household, Student


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = [
            "id",
            "household",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_primary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "household",
            "first_name",
            "last_name",
            "grade_level",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class HouseholdSerializer(serializers.ModelSerializer):
    guardians = GuardianSerializer(many=True, read_only=True)
    students = StudentSerializer(many=True, read_only=True)

    class Meta:
        model = Household
        fields = [
            "id",
            "name",
            "address1",
            "address2",
            "city",
            "state",
            "postal_code",
            "is_active",
            "guardians",
            "students",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
