"""Health endpoint must fail closed on an unreachable database."""
from unittest.mock import patch

import pytest
from django.test import Client


@pytest.mark.django_db
def test_api_health_returns_200_when_database_probe_succeeds():
    response = Client().get("/api/health/")
    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["db"] == "ok"


@pytest.mark.django_db
def test_api_health_returns_503_when_database_probe_fails():
    with patch("crown_api.health_views.connection.cursor", side_effect=RuntimeError("synthetic unavailable")):
        response = Client().get("/api/health/")
    payload = response.json()
    assert response.status_code == 503
    assert payload["ok"] is False
    assert payload["status"] == "unhealthy"
    assert payload["db"] == "unreachable"
    assert "build_sha" in payload
    assert "artifact_build_sha" in payload
