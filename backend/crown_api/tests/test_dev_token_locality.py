"""Fail-closed local access guard for the demo-token endpoint (no DB needed)."""
from unittest.mock import patch

import pytest
from django.test import RequestFactory, override_settings

from crown_api.dev_token_views import _is_local_request, dev_token


HOSTS = ["localhost", "127.0.0.1", "[::1]", "external.example"]


@pytest.mark.parametrize(
    ("peer", "host"),
    [
        ("127.0.0.1", "localhost:8000"),
        ("127.0.0.1", "127.0.0.1:8000"),
        ("::1", "[::1]:8000"),
    ],
)
@override_settings(ALLOWED_HOSTS=HOSTS)
def test_direct_loopback_peer_and_host_allowed(peer, host):
    request = RequestFactory().post("/api/dev/token/", REMOTE_ADDR=peer, HTTP_HOST=host)
    assert _is_local_request(request) is True


@pytest.mark.parametrize(
    ("peer", "host"),
    [
        ("203.0.113.9", "localhost:8000"),
        ("203.0.113.9", "127.0.0.1:8000"),
        ("203.0.113.9", "[::1]:8000"),
        ("127.0.0.1", "external.example"),
        ("", "localhost:8000"),
    ],
)
@override_settings(ALLOWED_HOSTS=HOSTS)
def test_spoofed_or_nonlocal_requests_denied(peer, host):
    request = RequestFactory().post("/api/dev/token/", REMOTE_ADDR=peer, HTTP_HOST=host)
    assert _is_local_request(request) is False


@pytest.mark.parametrize(
    ("forwarded_header", "value"),
    [
        ("HTTP_X_FORWARDED_FOR", "203.0.113.9"),
        ("HTTP_X_REAL_IP", "203.0.113.9"),
        ("HTTP_FORWARDED", "for=203.0.113.9"),
        ("HTTP_X_FORWARDED_HOST", "localhost"),
        ("HTTP_X_FORWARDED_PORT", "8000"),
        ("HTTP_X_FORWARDED_PROTO", "http"),
    ],
)
@override_settings(ALLOWED_HOSTS=HOSTS)
def test_forwarded_clients_never_count_as_direct_localhost(forwarded_header, value):
    request = RequestFactory().post(
        "/api/dev/token/", REMOTE_ADDR="127.0.0.1", HTTP_HOST="localhost:8000",
        **{forwarded_header: value},
    )
    assert _is_local_request(request) is False


@pytest.mark.parametrize("peer,host,headers", [
    ("203.0.113.9", "localhost", {}),
    ("127.0.0.1", "localhost", {"HTTP_X_FORWARDED_FOR": "203.0.113.9"}),
    ("127.0.0.1", "external.example", {}),
])
@override_settings(ALLOWED_HOSTS=HOSTS, CROWN_DEMO_MODE=True, CROWN_DEMO_KEY="test-demo-key")
def test_endpoint_denies_nonlocal_even_with_correct_key_before_user_lookup(peer, host, headers):
    request = RequestFactory().post(
        "/api/dev/token/", REMOTE_ADDR=peer, HTTP_HOST=host,
        HTTP_X_DEMO_KEY="test-demo-key", **headers,
    )
    with patch("crown_api.dev_token_views.get_user_model") as user_lookup:
        response = dev_token(request)
    assert response.status_code == 404
    user_lookup.assert_not_called()


@override_settings(ALLOWED_HOSTS=HOSTS, CROWN_DEMO_MODE=True, CROWN_DEMO_KEY="test-demo-key")
def test_direct_loopback_still_requires_correct_key_before_user_lookup():
    request = RequestFactory().post(
        "/api/dev/token/", REMOTE_ADDR="127.0.0.1", HTTP_HOST="localhost",
        HTTP_X_DEMO_KEY="wrong-key",
    )
    with patch("crown_api.dev_token_views.get_user_model") as user_lookup:
        response = dev_token(request)
    assert response.status_code == 404
    user_lookup.assert_not_called()
