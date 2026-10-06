from django.urls import path
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from crown_api.auth_middleware import CrownAccessTokenAuthentication
from crown_api.exports.views import (
    HouseholdsCSVExportView,
    InvoicesCSVExportView,
    PaymentsQuickBooksCSVExportView,
)


class _AuthenticatedSchemaProbe(APIView):
    authentication_classes = [CrownAccessTokenAuthentication]
    permission_classes = []

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response({"ok": True})


def _schema_for(patterns):
    return SchemaGenerator(patterns=patterns).get_schema(request=None, public=True)


def test_crown_access_token_authentication_is_registered_in_openapi():
    schema = _schema_for(
        [path("schema-probe/", _AuthenticatedSchemaProbe.as_view(), name="schema-probe")]
    )

    schemes = schema["components"]["securitySchemes"]
    assert schemes["CrownAccessTokenAuthentication"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "CROWN access token supplied in the Authorization Bearer header.",
    }
    assert {"CrownAccessTokenAuthentication": []} in schema["paths"]["/schema-probe/"]["get"]["security"]


def test_csv_exports_publish_text_csv_contracts_including_inherited_view():
    schema = _schema_for(
        [
            path("exports/invoices.csv", InvoicesCSVExportView.as_view(), name="invoices"),
            path("exports/households.csv", HouseholdsCSVExportView.as_view(), name="households"),
            path(
                "exports/accounting/payments-qb.csv",
                PaymentsQuickBooksCSVExportView.as_view(),
                name="payments-qb",
            ),
        ]
    )

    for endpoint in (
        "/exports/invoices.csv",
        "/exports/households.csv",
        "/exports/accounting/payments-qb.csv",
    ):
        content = schema["paths"][endpoint]["get"]["responses"]["200"]["content"]
        assert "text/csv" in content
        assert content["text/csv"]["schema"]["type"] == "string"
        assert content["text/csv"]["schema"]["format"] == "binary"
