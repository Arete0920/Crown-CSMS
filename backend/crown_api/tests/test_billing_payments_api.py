import pytest

pytestmark = pytest.mark.django_db


def test_requires_auth_billing_open_invoices(client):
    r = client.get("/api/billing/households/00000000-0000-0000-0000-000000000000/open-invoices/")
    assert r.status_code in (401, 403)
