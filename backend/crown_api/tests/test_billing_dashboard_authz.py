"""Billing dashboard totals require an explicit same-school billing.view grant."""

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crown_api.dashboards import views
from crown_api.dashboards.payload_contract import build_dashboard_payload, metric


def _principal(school, role_code, username, *, is_staff=False):
    user = UserAccount.objects.create_user(
        username=username, email=f"{username}@example.invalid", school=school, is_staff=is_staff
    )
    if role_code:
        UserRole.objects.create(user=user, school=school, role_code=role_code)
    client = APIClient(SERVER_PORT="443", **{"wsgi.url_scheme": "https"})
    # Production tenant middleware authenticates before DRF force_authenticate runs.
    # Use the real Django test session to reach both middleware and view grants.
    client.force_login(user)
    return client


@pytest.mark.django_db
@override_settings(TENANT_HEADER_REQUIRED=True, CROWN_ENV="production", CROWN_DEV_OPEN_API=False)
def test_billing_dashboard_requires_same_school_read_grant_before_live_data(monkeypatch):
    home = School.objects.create(name="Synthetic billing home")
    foreign_school = School.objects.create(name="Synthetic billing foreign")
    allowed_role = "BILLING_READER_TEST"
    grant, _ = CrownPermission.objects.get_or_create(code="billing.view")
    RolePermission.objects.get_or_create(role_code=allowed_role, permission=grant)

    builder_calls = []

    def synthetic_live_billing(school_id):
        builder_calls.append(str(school_id))
        return build_dashboard_payload(
            dashboard_key="billing",
            metrics=[metric("Outstanding Balances", "BILLING_PRIVATE_SENTINEL")],
            alerts=[],
            queue=[],
            meta={"school_id": str(school_id), "served_from": "live_db"},
        )

    monkeypatch.setitem(views.DASHBOARD_PAYLOAD_BUILDERS, "billing", synthetic_live_billing)
    url = reverse("dashboard-summary", kwargs={"dashboard_key": "billing"})
    granted = _principal(home, allowed_role, "synthetic-billing-granted")
    ungranted_staff = _principal(
        home, None, "synthetic-billing-ungranted-staff", is_staff=True
    )
    foreign = _principal(
        foreign_school, allowed_role, "synthetic-billing-foreign"
    )

    allowed = granted.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert allowed.status_code == 200
    assert allowed.json()["metrics"][0]["value"] == "BILLING_PRIVATE_SENTINEL"
    assert builder_calls == [str(home.id)]

    denied = ungranted_staff.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert denied.status_code == 403
    assert b"BILLING_PRIVATE_SENTINEL" not in denied.content

    cross_school = foreign.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert cross_school.status_code in (403, 404)
    assert b"BILLING_PRIVATE_SENTINEL" not in cross_school.content

    no_header = granted.get(url)
    assert no_header.status_code == 400
    invalid_header = granted.get(url, HTTP_X_SCHOOL_ID="not-a-uuid")
    assert invalid_header.status_code == 400

    anonymous = APIClient(SERVER_PORT="443", **{"wsgi.url_scheme": "https"})
    without_login = anonymous.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert without_login.status_code in (401, 403)
    assert b"BILLING_PRIVATE_SENTINEL" not in without_login.content
    assert builder_calls == [str(home.id)]
