from rest_framework import serializers

from admissions.models import AdmissionsApplication


class AdmissionsApplicationLinkReadSerializer(serializers.ModelSerializer):
    household_id = serializers.UUIDField(source="household.id", read_only=True, allow_null=True)
    household_name = serializers.CharField(
        source="household.household_name", read_only=True, allow_null=True
    )

    student_id = serializers.UUIDField(source="sis_student.id", read_only=True, allow_null=True)
    student_first_name = serializers.CharField(
        source="sis_student.person.first_name", read_only=True, allow_null=True
    )
    student_last_name = serializers.CharField(
        source="sis_student.person.last_name", read_only=True, allow_null=True
    )

    applicant_name = serializers.CharField(source="family.family_name", read_only=True)

    class Meta:
        model = AdmissionsApplication
        fields = (
            "id",
            "applicant_name",
            "status",
            "household_id",
            "household_name",
            "student_id",
            "student_first_name",
            "student_last_name",
        )
