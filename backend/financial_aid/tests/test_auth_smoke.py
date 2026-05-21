# backend/financial_aid/tests/test_auth_smoke.py
"""
Auth smoke tests for Phase 4B financial-aid endpoints.

Asserts that every /api/financial-aid/... endpoint rejects unauthenticated
requests. Acceptable responses are:
  400 → tenant-header/middleware fail-closed deny
  302 → Django login_required redirect to /accounts/login/  (session auth)
  401 → DRF IsAuthenticated / TokenAuthentication
  403 → DRF permission denied

NOT acceptable:
  404 → route is dead (include dropped from api_urls.py)
  200 → auth wall missing entirely
  500 → server error

The financial_aid views use Django's @login_required decorator (session auth),
so 302 is the expected production behaviour. This test would catch a regression
where a refactor swapped in an AllowAny permission or dropped the decorator.
"""
import uuid

import pytest
from rest_framework.test import APIClient

BILLING_RUN_ID = str(uuid.uuid4())

# (method, path)
ENDPOINTS = [
    ("GET",  "/api/financial-aid/applications/"),
    ("GET",  "/api/financial-aid/awards/"),
    ("POST", f"/api/financial-aid/billing-runs/{BILLING_RUN_ID}/disburse/"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("method,path", ENDPOINTS)
def test_unauthenticated_request_returns_auth_error(method, path):
    """
    An unauthenticated request must be denied by auth/tenant wall.

    - 404 → route is dead (URL wiring broken)
    - 200/500 → auth/permission wiring broken
    """
    client = APIClient()  # no credentials
    response = getattr(client, method.lower())(path, format="json")

    assert response.status_code in (400, 302, 401, 403), (
        f"{method} {path!r} returned HTTP {response.status_code}.\n"
        f"Expected 400/302/401/403 (auth/tenant wall).\n"
        f"  404 → route not wired into api_urls.py\n"
        f"  200 → @login_required / permission class missing\n"
        f"  500 → server error (check logs)"
    )

    # If Django session-auth redirect, verify it points to the canonical login URL.
    # A redirect to an unexpected location means middleware is misconfigured.
    if response.status_code == 302:
        location = response.get("Location", "")
        assert "/accounts/login/" in location, (
            f"{method} {path!r} returned 302 but redirected to unexpected location.\n"
            f"  Got:      {location!r}\n"
            f"  Expected: URL containing '/accounts/login/'"
        )
