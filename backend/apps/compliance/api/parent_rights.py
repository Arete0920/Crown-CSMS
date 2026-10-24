from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compliance.models import ConsentAudit
from households.scoping import get_request_school_id


class ParentDataRightsRequestSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(choices=("export", "correction", "deletion"))


class ParentDataRightsReceiptSerializer(serializers.Serializer):
    status = serializers.CharField()
    request_type = serializers.CharField()
    request_id = serializers.CharField()


class ParentDataRightsRequestView(APIView):
    """Record a school-scoped request receipt, never a grant of consent."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ParentDataRightsRequestSerializer,
        responses={202: ParentDataRightsReceiptSerializer},
    )
    def post(self, request):
        school_id = get_request_school_id(request, required=True)
        serializer = ParentDataRightsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_type = serializer.validated_data["request_type"]

        receipt = ConsentAudit.objects.create(
            tenant_id=str(school_id),
            consent_type="data_rights_request",
            version="2026.10",
            user=request.user,
            metadata={"request_type": request_type, "status": "received"},
        )

        return Response(
            {
                "status": "received",
                "request_type": request_type,
                "request_id": str(receipt.pk),
            },
            status=status.HTTP_202_ACCEPTED,
        )
