from rest_framework import serializers
from .models import ServiceEntry


class ServiceEntrySerializer(serializers.ModelSerializer):
	class Meta:
		model = ServiceEntry
		fields = [
			"id", "school", "student", "date", "hours",
			"category", "organization", "supervisor_name",
			"supervisor_contact", "notes", "status",
			"approved_by", "approved_at", "created_at",
		]
		read_only_fields = ["id", "created_at"]
