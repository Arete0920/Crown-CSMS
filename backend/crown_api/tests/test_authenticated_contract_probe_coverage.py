from __future__ import annotations

import json
from types import SimpleNamespace

from crown_api import authenticated_contract_probe as probe


class FakeResponse:
    def __init__(self, status_code, payload=None, content_type="application/json"):
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.charset = "utf-8"
        self.content = json.dumps(payload).encode("utf-8") if payload is not None else b""


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.logged_in_user = None

    def force_login(self, user):
        self.logged_in_user = user

    def generic(self, method, path, **extra):
        self.calls.append((method, path, extra))
        return self.responses.pop(0)


def test_normalize_path_and_wsgi_header_name():
    assert probe.normalize_path("") == ""
    assert probe.normalize_path("api//items/") == "/api/items"
    assert probe.normalize_path("/") == "/"
    assert probe.to_wsgi_header_name("X-School-Id") == "HTTP_X_SCHOOL_ID"
    assert probe.to_wsgi_header_name("") == ""


def test_json_kind_and_validation_reject_invalid_shapes():
    assert probe._get_json_kind({}) == "object"
    assert probe._get_json_kind([]) == "array"
    assert probe._get_json_kind(None) == "null"
    assert probe._get_json_kind(True) == "boolean"
    assert probe._get_json_kind(3) == "number"
    assert probe._get_json_kind("x") == "string"

    _, kind, errors = probe._validate_json_api_response(
        FakeResponse(200, {}, "application/json"), {"object"}
    )
    assert kind == "object"
    assert errors == ["status 200 but JSON object is empty"]

    _, kind, errors = probe._validate_json_api_response(
        FakeResponse(200, [1], "text/html"), {"array"}
    )
    assert kind is None
    assert errors == ["status 200 but non-JSON content type: text/html"]


def test_probe_entry_accepts_fail_closed_missing_header_and_valid_json():
    client = FakeClient(
        [
            FakeResponse(400, {"detail": "school required"}),
            FakeResponse(200, {"ok": True}),
        ]
    )
    user = SimpleNamespace(id=1)
    entry = {
        "moduleKey": "sample",
        "path": "/sample",
        "apiPrefix": "/api/sample/",
        "probeMethod": "get",
        "requiresAuth": True,
        "requiresSchoolHeader": True,
        "schoolHeaderName": "X-School-Id",
        "probeSchoolId": "school-a",
        "acceptableMissingSchoolHeaderStatusCodes": [400, 403],
        "acceptableAuthenticatedStatusCodes": [200],
        "expectedJsonTopLevelKinds": ["object"],
    }

    result = probe.probe_authenticated_contract_entry(entry, client=client, user=user)

    assert client.logged_in_user is user
    assert result["missingSchoolHeaderStatusCode"] == 400
    assert result["authenticatedStatusCode"] == 200
    assert result["authenticatedJsonKind"] == "object"
    assert result["errors"] == []
    assert client.calls[1][2]["HTTP_X_SCHOOL_ID"] == "school-a"


def test_probe_entry_reports_redirect_and_server_failures():
    client = FakeClient(
        [
            FakeResponse(302, None, "text/html"),
            FakeResponse(500, {"detail": "boom"}),
        ]
    )
    entry = {
        "moduleKey": "bad",
        "path": "/bad",
        "apiPrefix": "/api/bad/",
        "requiresAuth": False,
        "requiresSchoolHeader": True,
        "acceptableMissingSchoolHeaderStatusCodes": [400],
        "acceptableAuthenticatedStatusCodes": [200],
    }

    result = probe.probe_authenticated_contract_entry(
        entry, client=client, user=SimpleNamespace(id=1)
    )

    assert "missing-school-header status 302; expected one of [400]" in result["errors"]
    assert "endpoint redirected without school header" in result["errors"]
    assert "authenticated status 500; expected one of [200]" in result["errors"]
    assert "endpoint returned 5xx with auth/header" in result["errors"]


def test_failure_filter_and_summary_counts(monkeypatch):
    findings = [
        {"errors": [], "authenticatedStatusCode": 200, "missingSchoolHeaderStatusCode": 400},
        {"errors": ["bad"], "authenticatedStatusCode": 403, "missingSchoolHeaderStatusCode": 403},
        {"errors": [], "authenticatedStatusCode": 200, "missingSchoolHeaderStatusCode": None},
    ]
    monkeypatch.setattr(probe, "probe_authenticated_contract", lambda client=None: findings)

    assert probe.get_authenticated_contract_failures() == [findings[1]]
    assert probe.get_authenticated_contract_summary() == {
        "probedEntryCount": 3,
        "failureCount": 1,
        "authenticatedStatusCounts": {"200": 2, "403": 1},
        "missingHeaderStatusCounts": {"400": 1, "403": 1, "None": 1},
    }
