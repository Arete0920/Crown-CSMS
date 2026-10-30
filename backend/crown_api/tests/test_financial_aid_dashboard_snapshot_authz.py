"""Financial-aid dashboard snapshots require a persisted school-scoped grant."""
import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crown_api.dashboards.models import DashboardSnapshot


pytestmark = pytest.mark.django_db


def _principal(school, role_code, username):
    user = UserAccount.objects.create_user(username=username, school=school)
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    client = APIClient(SERVER_PORT="443", **{"wsgi.url_scheme": "https"})
    client.force_authenticate(user=user)
    return user, client


@override_settings(TENANT_HEADER_REQUIRED=True, CROWN_ENV="production", CROWN_DEV_OPEN_API=False)
def test_financial_aid_snapshot_requires_same_school_read_grant():
    home = School.objects.create(name="Synthetic aid home")
    other = School.objects.create(name="Synthetic aid foreign")
    allowed_role = "AID_DIRECTOR"
    ungranted_role = "TEACHER"
    grant, _ = CrownPermission.objects.get_or_create(code="financial_aid.view")
    RolePermission.objects.get_or_create(role_code=allowed_role, permission=grant)

    DashboardSnapshot.objects.create(
        school_id=str(home.id),
        dashboard_key="financial-aid",
        source="synthetic-test",
        payload={
            "dashboard_key": "financial-aid",
            "metrics": [{"label": "Sentinel", "value": "SENSITIVE_AID_SENTINEL"}],
            "alerts": [],
            "queue": [],
            "meta": {},
        },
    )
    url = reverse("dashboard-summary", kwargs={"dashboard_key": "financial-aid"})
    _, allowed = _principal(home, allowed_role, "aid-snapshot-granted")
    _, denied = _principal(home, ungranted_role, "aid-snapshot-ungranted")
    _, foreign = _principal(other, allowed_role, "aid-snapshot-foreign")

    response = allowed.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert response.status_code == 200
    assert response.json()["metrics"][0]["value"] == "SENSITIVE_AID_SENTINEL"

    response = denied.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert response.status_code == 403
    assert b"SENSITIVE_AID_SENTINEL" not in response.content

    response = foreign.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert response.status_code in (403, 404)
    assert b"SENSITIVE_AID_SENTINEL" not in response.content

    anonymous = APIClient(SERVER_PORT="443", **{"wsgi.url_scheme": "https"})
    response = anonymous.get(url, HTTP_X_SCHOOL_ID=str(home.id))
    assert response.status_code in (401, 403)
    assert b"SENSITIVE_AID_SENTINEL" not in response.content
