from rest_framework import serializers

from crown_api.models import Household, HouseholdMember, Person, Student


class HouseholdMemberReadSerializer(serializers.ModelSerializer):
    person_id = serializers.UUIDField(source="person.id", read_only=True)
    first_name = serializers.CharField(source="person.first_name", read_only=True)
    last_name = serializers.CharField(source="person.last_name", read_only=True)
    email = serializers.EmailField(source="person.email", read_only=True)
    phone = serializers.CharField(source="person.phone", read_only=True)

    class Meta:
        model = HouseholdMember
        fields = [
            "person_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_primary",
        ]


class StudentReadSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="id", read_only=True)
    person_id = serializers.UUIDField(source="person.id", read_only=True)
    first_name = serializers.CharField(source="person.first_name", read_only=True)
    last_name = serializers.CharField(source="person.last_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "student_id",
            "person_id",
            "first_name",
            "last_name",
            "grade_level",
            "active",
        ]


class HouseholdReadSerializer(serializers.ModelSerializer):
    members = HouseholdMemberReadSerializer(many=True, read_only=True)
    students = StudentReadSerializer(many=True, read_only=True)

    class Meta:
        model = Household
        fields = [
            "id",
            "household_name",
            "primary_address_line1",
            "primary_address_line2",
            "primary_city",
            "primary_state",
            "primary_postal_code",
            "members",
            "students",
        ]
