from rest_framework import serializers
from .models import ReenrollmentSession


class ReenrollmentSessionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReenrollmentSession
		fields = [
			"id", "school", "created_by",
			"target_year_label", "enrollment_fee",
			"excluded_ids", "candidates_snapshot",
			"commit_result", "status",
			"created_at", "updated_at",
		]
		read_only_fields = [
			"id", "candidates_snapshot", "commit_result",
			"created_at", "updated_at",
		]
