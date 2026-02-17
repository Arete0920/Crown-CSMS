from __future__ import annotations
from rest_framework import serializers
from servicehours.models import ServiceEntry

class ServiceEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceEntry
        fields = [
            "id","student","student_name","date","hours","category","organization",
            "supervisor_name","supervisor_contact","notes","status","approved_by","approved_at","created_at"
        ]
        read_only_fields = ["approved_by","approved_at","created_at"]

    def get_student_name(self, obj):
        for attr in ["full_name", "name"]:
            if hasattr(obj.student, attr):
                return getattr(obj.student, attr)
        first = getattr(obj.student, "first_name", "")
        last = getattr(obj.student, "last_name", "")
        return (first + " " + last).strip() or str(obj.student_id)

class ServiceApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["approved","rejected"])
    note = serializers.CharField(required=False, allow_blank=True)
