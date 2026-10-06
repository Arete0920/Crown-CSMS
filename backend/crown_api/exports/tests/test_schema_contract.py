import pytest
from drf_spectacular.generators import SchemaGenerator

from crown_api.exports.urls import urlpatterns


@pytest.mark.django_db
def test_csv_export_routes_publish_binary_csv_contracts():
    schema = SchemaGenerator(patterns=urlpatterns).get_schema(request=None, public=True)

    expected_paths = {
        "/exports/invoices.csv",
        "/exports/installment-schedule.csv",
        "/exports/households.csv",
        "/exports/students.csv",
        "/exports/staff.csv",
        "/exports/ledger-charges.csv",
        "/exports/ledger-allocations.csv",
        "/exports/payments.csv",
        "/exports/statements.csv",
        "/exports/statement-lines.csv",
        "/exports/year-end/tuition-paid.csv",
        "/exports/accounting/payments-qb.csv",
    }

    assert expected_paths.issubset(schema["paths"])

    for path in expected_paths:
        response = schema["paths"][path]["get"]["responses"]["200"]
        csv_content = response["content"]["text/csv"]
        assert csv_content["schema"] == {"type": "string", "format": "binary"}
