from unittest.mock import patch
import uuid

import pytest
from django.core.cache import cache
from django.test import Client
from django.contrib.auth.hashers import make_password

from crown_api.auth_models import CrownUser
from crown_api.jwt_utils import build_refresh_token

pytestmark = pytest.mark.django_db


def test_legacy_login_rate_limits_repeated_attempts():
    cache.clear()
    client = Client()

    for _ in range(10):
        response = client.post(
            "/api/auth/login/",
            data={"email": "missing@example.test", "password": "wrong"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.10",
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/auth/login/",
        data={"email": "missing@example.test", "password": "wrong"},
        content_type="application/json",
        REMOTE_ADDR="203.0.113.10",
    )

    assert blocked.status_code == 429
    assert blocked.json()["error"] == "rate_limited"
    assert blocked["Retry-After"] == "60"


def test_simplejwt_token_issue_rate_limits_repeated_attempts():
    cache.clear()
    client = Client()

    for _ in range(10):
        response = client.post(
            "/api/v1/auth/token/",
            data={"username": "missing@example.test", "password": "wrong"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.11",
        )
        assert response.status_code in (400, 401)

    blocked = client.post(
        "/api/v1/auth/token/",
        data={"username": "missing@example.test", "password": "wrong"},
        content_type="application/json",
        REMOTE_ADDR="203.0.113.11",
    )

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "rate_limited"
    assert blocked["Retry-After"] == "60"


def test_legacy_refresh_rate_limits_invalid_tokens():
    cache.clear()
    client = Client()

    for _ in range(10):
        response = client.post(
            "/api/auth/refresh/",
            data={"refresh": "invalid-refresh-token"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.12",
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/auth/refresh/",
        data={"refresh": "invalid-refresh-token"},
        content_type="application/json",
        REMOTE_ADDR="203.0.113.12",
    )

    assert blocked.status_code == 429
    assert blocked.json()["error"] == "rate_limited"
    assert blocked["Retry-After"] == "60"


def test_legacy_refresh_replay_remains_rate_limited():
    cache.clear()
    user = CrownUser.objects.create(
        email="refresh-rate-limit@example.test",
        password_hash=make_password("Passw0rd!"),
        role="staff",
        school_id=uuid.uuid4(),
        is_active=True,
    )
    token = build_refresh_token(user_id=str(user.id))
    client = Client()

    assert client.post(
        "/api/auth/refresh/",
        data={"refresh": token},
        content_type="application/json",
        REMOTE_ADDR="203.0.113.26",
    ).status_code == 200

    for _ in range(10):
        replay = client.post(
            "/api/auth/refresh/",
            data={"refresh": token},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.26",
        )
        assert replay.status_code == 401

    blocked = client.post(
        "/api/auth/refresh/",
        data={"refresh": token},
        content_type="application/json",
        REMOTE_ADDR="203.0.113.26",
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "rate_limited"


def test_simplejwt_refresh_rate_limits_invalid_tokens():
    cache.clear()
    client = Client()

    for _ in range(20):
        response = client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": "invalid-refresh-token"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.13",
        )
        assert response.status_code in (400, 401)

    blocked = client.post(
        "/api/v1/auth/token/refresh/",
        data={"refresh": "invalid-refresh-token"},
        content_type="application/json",
        REMOTE_ADDR="203.0.113.13",
    )

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "rate_limited"
    assert blocked["Retry-After"] == "60"


def test_legacy_login_fails_closed_when_rate_limit_cache_read_fails():
    client = Client()
    with patch("crown_api.auth_rate_limit.cache.get", side_effect=RuntimeError("cache unavailable")):
        response = client.post(
            "/api/auth/login/",
            data={"email": "missing@example.test", "password": "wrong"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.20",
        )

    assert response.status_code == 503
    assert response.json()["error"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"


def test_simplejwt_login_fails_closed_when_rate_limit_cache_read_fails():
    client = Client()
    with patch("crown_api.auth_rate_limit.cache.get", side_effect=RuntimeError("cache unavailable")):
        response = client.post(
            "/api/v1/auth/token/",
            data={"username": "missing@example.test", "password": "wrong"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.21",
        )

    assert response.status_code == 503
    assert response.json()["code"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"


def test_invalid_login_fails_closed_when_failure_counter_write_fails():
    cache.clear()
    client = Client()
    with patch("crown_api.auth_rate_limit.cache.add", side_effect=RuntimeError("cache write unavailable")):
        response = client.post(
            "/api/auth/login/",
            data={"email": "missing@example.test", "password": "wrong"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.22",
        )

    assert response.status_code == 503
    assert response.json()["error"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"


def test_legacy_refresh_fails_closed_when_rate_limit_cache_read_fails():
    client = Client()
    with patch("crown_api.auth_rate_limit.cache.get", side_effect=RuntimeError("cache unavailable")):
        response = client.post(
            "/api/auth/refresh/",
            data={"refresh": "invalid-refresh-token"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.23",
        )

    assert response.status_code == 503
    assert response.json()["error"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"


def test_simplejwt_refresh_fails_closed_when_rate_limit_cache_read_fails():
    client = Client()
    with patch("crown_api.auth_rate_limit.cache.get", side_effect=RuntimeError("cache unavailable")):
        response = client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": "invalid-refresh-token"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.24",
        )

    assert response.status_code == 503
    assert response.json()["code"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"


def test_simplejwt_refresh_fails_closed_when_failure_counter_write_fails():
    cache.clear()
    client = Client()
    with patch("crown_api.auth_rate_limit.cache.add", side_effect=RuntimeError("cache write unavailable")):
        response = client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": "invalid-refresh-token"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.25",
        )

    assert response.status_code == 503
    assert response.json()["code"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"
