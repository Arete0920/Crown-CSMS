import json
from pathlib import Path

import pytest
from django.test import Client, override_settings


pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@override_settings(ROOT_URLCONF="release_closeout.urls")
@pytest.mark.django_db
def test_release_closeout_status_endpoint():
    client = Client()
    res = client.get("/api/v1/release-closeout/status/")
    assert res.status_code == 200
    payload = res.json()
    assert payload["discipline_escalation"] is True
    assert payload["transcript_export"] is True
    assert payload["report_card_export"] is True
    assert payload["graduation_readiness"] is True


@override_settings(ROOT_URLCONF="release_closeout.urls")
@pytest.mark.django_db
def test_release_closeout_live_metrics_endpoint():
    client = Client()
    res = client.get("/api/v1/release-closeout/metrics/live/")
    assert res.status_code == 200
    payload = res.json()
    assert "backend_python_files" in payload
    assert "frontend_tsx_files" in payload
    assert "mock_or_seed_hits" in payload


@override_settings(ROOT_URLCONF="release_closeout.urls")
@pytest.mark.django_db
@pytest.mark.parametrize("route", [
    "/api/v1/reports/transcript/DEMO-001/",
    "/api/v1/reports/report-card/DEMO-001/",
    "/api/v1/reports/discipline/DEMO-001/",
    "/api/v1/reports/board/",
])
def test_pdf_endpoints(route):
    client = Client()
    res = client.get(route)
    assert res.status_code == 200
    assert res["Content-Type"] == "application/pdf"


@override_settings(ROOT_URLCONF="release_closeout.urls")
@pytest.mark.django_db
def test_sms_status_endpoint():
    client = Client()
    res = client.get("/api/v1/notifications/sms/status/")
    assert res.status_code == 200
    payload = res.json()
    assert payload["green"] is True


def test_priority_doc_exists():
    assert Path("docs/release/PRIORITY_16_31_TO_GREEN.md").exists()