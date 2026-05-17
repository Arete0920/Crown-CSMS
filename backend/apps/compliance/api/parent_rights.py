from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compliance.services.consent_service import record_consent


class ParentDataRightsRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_type = request.data.get("request_type")

        allowed = ["export", "correction", "deletion"]

        if request_type not in allowed:
            return Response({"detail": "Invalid request type."}, status=400)

        tenant = getattr(request, "tenant", None)
        tenant_id = str(getattr(tenant, "id", "unknown"))

        record_consent(
            tenant_id=tenant_id,
            consent_type="parental_consent",
            version="2026.05",
            user=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
            metadata={"request_type": request_type},
        )

        return Response({"status": "accepted", "request_type": request_type})
