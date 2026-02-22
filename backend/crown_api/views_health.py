from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
import os

try:
	from crown_api.build_info import BUILD_SHA
except Exception:
	BUILD_SHA = "unknown"


def health_proof(request):
	db_status = "ok"
	try:
		with connection.cursor() as cursor:
			cursor.execute("SELECT 1;")
			cursor.fetchone()
	except Exception:
		db_status = "error"

	environment = os.getenv("ENVIRONMENT", "unknown")

	return JsonResponse(
		{
			"status": "ok",
			"build_sha": BUILD_SHA,
			"environment": environment,
			"db": db_status,
			"timestamp": timezone.now().isoformat(),
		},
		status=200,
	)
