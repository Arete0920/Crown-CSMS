from rest_framework import serializers
from .models import ImportSession


class ImportSessionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ImportSession
		fields = [
			"id", "school", "created_by", "mode", "status",
			"filename", "rows_total", "students_detected",
			"guardians_detected", "households_detected",
			"validate_result", "commit_result",
			"created_at", "updated_at",
		]
		read_only_fields = [
			"id", "rows_total", "students_detected",
			"guardians_detected", "households_detected",
			"validate_result", "commit_result",
			"created_at", "updated_at",
		]
