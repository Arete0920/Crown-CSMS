from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from admissions.models import AdmissionsApplication


class AdmissionsApplicationLinkReadSerializer(serializers.ModelSerializer):
    academic_year_id = serializers.UUIDField(source="academic_year.id", read_only=True)
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
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    guardian_contacts = serializers.SerializerMethodField()
    primary_guardian_name = serializers.SerializerMethodField()
    primary_guardian_email = serializers.SerializerMethodField()
    primary_guardian_phone = serializers.SerializerMethodField()

    @staticmethod
    def _guardian_contacts_for_obj(obj):
        household = getattr(obj, "household", None)
        if household is None:
            return []

        members = getattr(household, "members", None)
        if members is None:
            return []

        contacts = []
        for member in members.all():
            role = getattr(member, "role", "") or ""
            if role not in ("PRIMARY_GUARDIAN", "GUARDIAN"):
                continue

            person = getattr(member, "person", None)
            if person is None:
                continue

            first_name = (getattr(person, "first_name", "") or "").strip()
            last_name = (getattr(person, "last_name", "") or "").strip()
            full_name = f"{first_name} {last_name}".strip()

            contacts.append(
                {
                    "name": full_name,
                    "email": getattr(person, "email", "") or "",
                    "phone": getattr(person, "phone", "") or "",
                    "is_primary": bool(getattr(member, "is_primary", False)),
                    "role": role,
                }
            )

        contacts.sort(key=lambda c: (not c["is_primary"], c["name"].lower()))
        return contacts

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_guardian_contacts(self, obj):
        return self._guardian_contacts_for_obj(obj)

    def _get_primary_guardian(self, obj):
        contacts = self._guardian_contacts_for_obj(obj)
        if not contacts:
            return {}
        return contacts[0]

    @extend_schema_field(serializers.CharField())
    def get_primary_guardian_name(self, obj):
        return self._get_primary_guardian(obj).get("name", "")

    @extend_schema_field(serializers.CharField())
    def get_primary_guardian_email(self, obj):
        return self._get_primary_guardian(obj).get("email", "")

    @extend_schema_field(serializers.CharField())
    def get_primary_guardian_phone(self, obj):
        return self._get_primary_guardian(obj).get("phone", "")

    class Meta:
        model = AdmissionsApplication
        fields = (
            "id",
            "academic_year_id",
            "applicant_name",
            "status",
            "household_id",
            "household_name",
            "student_id",
            "student_first_name",
            "student_last_name",
            "created_at",
            "updated_at",
            "guardian_contacts",
            "primary_guardian_name",
            "primary_guardian_email",
            "primary_guardian_phone",
        )
