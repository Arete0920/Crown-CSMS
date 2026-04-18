import pytest
from django.test import Client, override_settings

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

PDF_ROUTES = [
    "/api/v1/reports/transcript/DEMO-001/",
    "/api/v1/reports/report-card/DEMO-001/",
    "/api/v1/reports/discipline/DEMO-001/",
    "/api/v1/reports/board/",
]

JSON_ROUTES = [
    "/api/v1/release-closeout/status/",
    "/api/v1/release-closeout/metrics/live/",
    "/api/v1/release-closeout/graduation/DEMO-001/",
    "/api/v1/release-closeout/discipline/DEMO-001/",
    "/api/v1/notifications/sms/status/",
]


@override_settings(ROOT_URLCONF="release_closeout.urls", TENANT_HEADER_REQUIRED=False, SECURE_SSL_REDIRECT=False)
@pytest.mark.django_db
@pytest.mark.parametrize("route", JSON_ROUTES)
def test_release_json_routes(route):
    client = Client()
    response = client.get(route)
    assert response.status_code == 200
    assert "application/json" in response["Content-Type"]


@override_settings(ROOT_URLCONF="release_closeout.urls", TENANT_HEADER_REQUIRED=False, SECURE_SSL_REDIRECT=False)
@pytest.mark.django_db
@pytest.mark.parametrize("route", PDF_ROUTES)
def test_release_pdf_routes(route):
    client = Client()
    response = client.get(route)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert "attachment;" in response["Content-Disposition"].lower()