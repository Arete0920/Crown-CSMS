import pytest
from drf_spectacular.generators import SchemaGenerator

from apps.accounting.urls import urlpatterns


@pytest.mark.django_db
def test_accounting_routes_generate_explicit_openapi_contracts():
    schema = SchemaGenerator(patterns=urlpatterns).get_schema(request=None, public=True)

    expected_paths = {
        "/vendors/",
        "/funds/",
        "/dimensions/",
        "/purchase-orders/",
        "/purchase-orders/{po_id}/submit/",
        "/purchase-orders/{po_id}/approve/",
        "/bills/",
        "/bills/{bill_id}/approve/",
        "/bills/{bill_id}/post/",
        "/bills/{bill_id}/void/",
        "/budgets/",
        "/budgets/{budget_id}/approve/",
        "/reports/trial-balance/",
        "/reports/income-statement/",
        "/reports/balance-sheet/",
        "/reports/budgets/{budget_id}/variance/",
    }

    assert expected_paths.issubset(schema["paths"])

    for path in expected_paths:
        for operation in schema["paths"][path].values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            assert operation["responses"], f"{path} is missing documented responses"

    assert "requestBody" in schema["paths"]["/vendors/"]["post"]
    assert "requestBody" in schema["paths"]["/purchase-orders/"]["post"]
    assert "requestBody" in schema["paths"]["/bills/"]["post"]
    assert "requestBody" in schema["paths"]["/budgets/"]["post"]
    assert "requestBody" not in schema["paths"]["/purchase-orders/{po_id}/submit/"]["post"]
    assert "requestBody" not in schema["paths"]["/budgets/{budget_id}/approve/"]["post"]

    trial_params = {
        parameter["name"]
        for parameter in schema["paths"]["/reports/trial-balance/"]["get"].get("parameters", [])
    }
    income_params = {
        parameter["name"]
        for parameter in schema["paths"]["/reports/income-statement/"]["get"].get("parameters", [])
    }
    balance_params = {
        parameter["name"]
        for parameter in schema["paths"]["/reports/balance-sheet/"]["get"].get("parameters", [])
    }
    assert {"start_date", "end_date"} <= trial_params
    assert {"start_date", "end_date"} <= income_params
    assert {"as_of"} <= balance_params
