from decimal import Decimal
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


class ServiceEntrySubmissionSerializer(serializers.Serializer):
    """Validate accounting inputs before creating a pending service entry.

    Student ownership and school assignment are enforced by the view.
    Decision fields and school are never accepted from the client.
    """
    student = serializers.UUIDField()
    date = serializers.DateField()
    hours = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.01"))
    category = serializers.CharField(max_length=80, required=False, allow_blank=True, default="Community Service")
    organization = serializers.CharField(max_length=120, required=False, allow_blank=True, default="Local Partner")
    supervisor_name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    supervisor_contact = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
