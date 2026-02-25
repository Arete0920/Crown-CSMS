# backend/financial_aid/tests/test_url_routes.py
"""
Guardrail: assert that all three Phase 4B financial-aid routes are wired
into the global URL router (crown_api/api_urls.py).

If any of these fail it means the app's urls.py was never included in the
project router — the exact silent regression that hit Phase 4B on first deploy.
"""
import uuid

import pytest
from django.urls import resolve, Resolver404


BILLING_RUN_ID = str(uuid.uuid4())

EXPECTED_ROUTES = [
    ("/api/financial-aid/applications/", "financial-aid-applications"),
    ("/api/financial-aid/awards/", "financial-aid-awards"),
    (
        f"/api/financial-aid/billing-runs/{BILLING_RUN_ID}/disburse/",
        "financial-aid-disburse-to-billing-run",
    ),
]


@pytest.mark.parametrize("path,expected_view_name", EXPECTED_ROUTES)
def test_financial_aid_route_resolves(path, expected_view_name):
    """
    Each financial-aid endpoint must resolve in the global URL tree.
    A Resolver404 means the route is dead — app urls.py not included.
    """
    try:
        match = resolve(path)
    except Resolver404:
        pytest.fail(
            f"Route not found: {path!r}\n"
            "Likely cause: financial_aid.urls is not included in crown_api/api_urls.py.\n"
            "Fix: add path('financial-aid/', include('financial_aid.urls')) to api_urls.py."
        )
    assert match.url_name == expected_view_name, (
        f"Route {path!r} resolved but to wrong view. "
        f"Expected url_name={expected_view_name!r}, got {match.url_name!r}."
    )
