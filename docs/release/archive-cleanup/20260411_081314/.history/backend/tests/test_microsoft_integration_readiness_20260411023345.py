import json

import pytest
from rest_framework.test import APIClient

from comms.models import OutboxMessage
from comms.tasks import _send
from core.models import School, UserAccount
from integrations import graph_client


pytestmark = pytest.mark.django_db


class _FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload or {}
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def test_graph_send_mail_accepts_azure_env_fallback(monkeypatch):
    monkeypatch.delenv("GRAPH_TENANT_ID", raising=False)
    monkeypatch.delenv("GRAPH_CLIENT_ID", raising=False)
    monkeypatch.delenv("GRAPH_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant-123")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client-123")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret-123")
    graph_client._TOKEN_CACHE.update({"ts": 0, "token": None, "exp": 0})

    calls = []

    def fake_post(url, data=None, headers=None, json=None, timeout=None):
        calls.append({"url": url, "data": data, "headers": headers, "json": json})
        if "oauth2" in url:
            return _FakeResponse({"access_token": "token-abc", "expires_in": 3600})
        return _FakeResponse({})

    monkeypatch.setattr(graph_client.requests, "post", fake_post)

    graph_client.send_mail(
        from_user="no-reply@example.com",
        to="family@example.com",
        subject="Hello",
        body_html="<p>Graph delivery works</p>",
    )

    assert len(calls) == 2
    assert calls[0]["url"].startswith("https://login.microsoftonline.com/tenant-123/")
    assert calls[1]["url"] == "https://graph.microsoft.com/v1.0/users/no-reply@example.com/sendMail"


def test_send_supports_teams_channel_payload(monkeypatch):
    sent = {}

    def fake_post_to_teams_channel(sender, team_id, channel_id, message):
        sent.update(
            {
                "sender": sender,
                "team_id": team_id,
                "channel_id": channel_id,
                "message": message,
            }
        )

    monkeypatch.setattr("comms.teams_service.post_to_teams_channel", fake_post_to_teams_channel)

    msg = OutboxMessage(
        school_id="11111111-1111-1111-1111-111111111111",
        channel="TEAMS",
        to=json.dumps({"team_id": "team-42", "channel_id": "channel-7"}),
        subject="Operations alert",
        body="<p>Heads up</p>",
        idempotency_key="teams-test-key",
    )

    _send(msg)

    assert sent["team_id"] == "team-42"
    assert sent["channel_id"] == "channel-7"
    assert sent["message"] == "<p>Heads up</p>"


def test_m365_services_status_route_exists_and_fails_closed_without_config(monkeypatch):
    for name in [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "GRAPH_TENANT_ID",
        "GRAPH_CLIENT_ID",
        "GRAPH_CLIENT_SECRET",
        "M365_DEFAULT_TENANT_ID",
        "M365_DEFAULT_CLIENT_ID",
        "M365_CLIENT_SECRET",
        "M365_SHAREPOINT_SITE_ID",
        "M365_DEFAULT_DRIVE_ID",
        "GRAPH_FROM_USER",
    ]:
        monkeypatch.delenv(name, raising=False)

    school = School.objects.create(name="Microsoft Readiness School")
    user = UserAccount.objects.create_user(
        username="m365audit",
        password="pass",
        email="m365audit@example.com",
        school=school,
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f"/api/v1/m365/services-status/", HTTP_X_SCHOOL_ID=str(school.id))

    assert response.status_code == 200, response.content
    payload = response.json()
    assert payload["outlook"] is False
    assert payload["sharepoint"] is False
    assert payload["teams"] is False
    assert payload["planner"] is False
