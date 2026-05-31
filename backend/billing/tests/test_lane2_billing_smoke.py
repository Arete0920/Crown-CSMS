import os
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_lane2_billing_endpoints_smoke__demo_mode(settings):
    """
    Lane 2 guard:
    - In DEMO_MODE, key billing + ledger endpoints must respond (200/401/403 acceptable, 404/5xx not acceptable).
    - This prevents "route exists but breaks" regressions.
    """
    settings.DEMO_MODE = True

    # If your project uses a different env var name, keep DEMO_MODE in settings and set here.
    os.environ["CROWN_DEMO_MODE"] = "true"

    client = APIClient()

    # NOTE: This test assumes your DEMO_MODE stack allows read access (as your demo wiring does).
    # If auth is still required in DEMO_MODE for these endpoints, swap this to fetch a dev token
    # and set Authorization here.
    school_id = getattr(settings, "DEMO_SCHOOL_ID", None) or os.environ.get("CROWN_DEMO_SCHOOL_ID")
    if not school_id:
        pytest.skip("DEMO school id not available (set settings.DEMO_SCHOOL_ID or env CROWN_DEMO_SCHOOL_ID)")

    client.credentials(HTTP_X_SCHOOL_ID=str(school_id))

    endpoints = [
        "/api/v1/billing/runs/",
        "/api/v1/billing/invoices/",
        "/api/v1/billing/installment-plans/",
        "/api/v1/ledger/charges/open/",
        "/api/v1/ledger/invoices/open/",
    ]

    for path in endpoints:
        resp = client.get(path)
        assert resp.status_code in (200, 401, 403), (
            f"{path} returned {resp.status_code}: {getattr(resp, 'data', resp.content)}"
        )
