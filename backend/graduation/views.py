from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from core.tenant_models import get_current_school
from .services import CreditAuditService

class GraduationAuditView(APIView):
    """
    GET /api/v1/graduation/audit/<student_id>/
    Returns a JSON audit: required credits, earned credits, remaining, and on_track flag.
    """
    authentication_classes = []  # project-level auth is handled elsewhere; keep consistent with current patterns
    permission_classes = []

    def get(self, request, student_id):
        school = get_current_school()
        if school is None:
            # If tenant middleware is configured, this should never happen; fail closed anyway.
            return JsonResponse({"detail": "TENANT_CONTEXT_MISSING"}, status=400)

        svc = CreditAuditService()
        result = svc.audit(student_id=student_id, school=school)

        # If we can't resolve student model or student doesn't exist, return 404 cleanly.
        if result.get("status") == "STUDENT_NOT_FOUND":
            return JsonResponse(result, status=404)

        if result.get("status") == "STUDENT_MODEL_UNRESOLVED":
            return JsonResponse(result, status=500)

        return JsonResponse(result, status=200)
