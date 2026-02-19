import os
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_lane2_payment_endpoints_no_redirect__demo_mode(settings):
    settings.DEMO_MODE = True
    os.environ["CROWN_DEMO_MODE"] = "true"

    school_id = getattr(settings, "DEMO_SCHOOL_ID", None) or os.environ.get("CROWN_DEMO_SCHOOL_ID")
    if not school_id:
        pytest.skip("DEMO school id not available (set settings.DEMO_SCHOOL_ID or env CROWN_DEMO_SCHOOL_ID)")

    client = APIClient()
    client.credentials(HTTP_X_SCHOOL_ID=str(school_id))

    # We are NOT asserting business logic here, just that endpoints do not redirect to login (302).
    # A 401/403 is acceptable for this guard if DEMO_MODE requires auth.
    paths = [
        "/api/v1/billing/payments/record/",
        "/api/v1/billing/payments/",
    ]

    for path in paths:
        resp = client.post(path, data={}, format="json")
        assert resp.status_code != 302, f"{path} redirected (session auth leak): {resp.status_code}"
