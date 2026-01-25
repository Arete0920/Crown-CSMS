from rest_framework import serializers

from crown_api.models import Student, StudentProfile


class StudentProfileReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = (
            "student_number",
            "birth_date",
            "start_date",
            "expected_grad_year",
        )


class StudentReadSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="id", read_only=True)
    person_id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(source="person.first_name", read_only=True)
    last_name = serializers.CharField(source="person.last_name", read_only=True)

    household_id = serializers.UUIDField(read_only=True)
    household_name = serializers.CharField(source="household.household_name", read_only=True)

    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        profile = getattr(obj, "profile", None)
        if profile is None:
            return None
        return StudentProfileReadSerializer(profile).data

    class Meta:
        model = Student
        fields = (
            "student_id",
            "person_id",
            "first_name",
            "last_name",
            "household_id",
            "household_name",
            "grade_level",
            "active",
            "profile",
        )
