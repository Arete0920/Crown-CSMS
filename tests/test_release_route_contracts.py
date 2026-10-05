import pytest
from django.test import Client, override_settings

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

RETIRED_ROUTES = [
    "/api/v1/release-closeout/status/",
    "/api/v1/release-closeout/metrics/live/",
    "/api/v1/release-closeout/graduation/DEMO-001/",
    "/api/v1/release-closeout/discipline/DEMO-001/",
    "/api/v1/reports/transcript/DEMO-001/",
    "/api/v1/reports/report-card/DEMO-001/",
    "/api/v1/reports/discipline/DEMO-001/",
    "/api/v1/reports/board/",
    "/api/v1/notifications/sms/status/",
]


@override_settings(TENANT_HEADER_REQUIRED=False, SECURE_SSL_REDIRECT=False)
@pytest.mark.django_db
@pytest.mark.parametrize("route", RETIRED_ROUTES)
def test_retired_release_scaffold_routes_are_not_exposed(route):
    response = Client().get(route)
    assert response.status_code == 404
