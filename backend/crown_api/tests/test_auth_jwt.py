# backend/crown_api/tests/test_auth_jwt.py
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.conf import settings
from django.db import OperationalError, close_old_connections, connection
from django.test import Client
from django.contrib.auth.hashers import make_password

from crown_api.auth_models import CrownUser
from crown_api.jwt_utils import decode_refresh, encode_jwt


pytestmark = pytest.mark.django_db


def _legacy_refresh_token(user_id, **claims):
    now = int(time.time())
    payload = {
        "typ": "refresh",
        "sub": str(user_id),
        "iat": now,
        "exp": now + 3600,
        **claims,
    }
    return encode_jwt(payload, secret=settings.SECRET_KEY + "|refresh")


def test_login_success_and_me_requires_token():
    school_id = uuid.uuid4()
    user = CrownUser.objects.create(
        email="admin@heritage.test",
        password_hash=make_password("Passw0rd!"),
        role="admin",
        school_id=school_id,
        is_active=True,
    )

    c = Client()

    # me without token -> 401
    r = c.get("/api/auth/me/")
    assert r.status_code == 401
    assert r.json()["error"] == "Unauthorized"

    # login -> tokens
    r = c.post(
        "/api/auth/login/",
        data={"email": "admin@heritage.test", "password": "Passw0rd!"},
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "access" in body and isinstance(body["access"], str) and len(body["access"]) > 20
    assert "refresh" in body and isinstance(body["refresh"], str) and len(body["refresh"]) > 20

    access = body["access"]

    # me with token -> 200
    r = c.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert r.status_code == 200
    me = r.json()
    assert me["ok"] is True
    assert me["user"]["email"] == "admin@heritage.test"
    assert me["user"]["role"] == "admin"
    assert me["user"]["school_id"] == str(school_id)


def test_login_rejects_bad_password():
    CrownUser.objects.create(
        email="user@x.test",
        password_hash=make_password("RightPass1!"),
        role="staff",
        school_id=uuid.uuid4(),
        is_active=True,
    )

    c = Client()
    r = c.post(
        "/api/auth/login/",
        data={"email": "user@x.test", "password": "wrong"},
        content_type="application/json",
    )
    assert r.status_code == 401
    assert r.json()["error"] == "invalid_credentials"


def test_refresh_rotates_token_rejects_replay_and_preserves_tenant_role():
    school_id = uuid.uuid4()
    CrownUser.objects.create(
        email="finance@x.test",
        password_hash=make_password("Cash1234!"),
        role="finance",
        school_id=school_id,
        is_active=True,
    )

    c = Client()
    r = c.post(
        "/api/auth/login/",
        data={"email": "finance@x.test", "password": "Cash1234!"},
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.json()
    refresh = body["refresh"]

    r = c.post(
        "/api/auth/refresh/",
        data={"refresh": refresh},
        content_type="application/json",
    )
    assert r.status_code == 200
    body2 = r.json()
    assert body2["ok"] is True
    assert "access" in body2 and len(body2["access"]) > 20
    assert body2["refresh"] != refresh

    # new access works on /me
    r = c.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {body2['access']}")
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "finance"
    assert r.json()["user"]["school_id"] == str(school_id)

    replay = c.post(
        "/api/auth/refresh/",
        data={"refresh": refresh},
        content_type="application/json",
    )
    assert replay.status_code == 401

    replacement = c.post(
        "/api/auth/refresh/",
        data={"refresh": body2["refresh"]},
        content_type="application/json",
    )
    assert replacement.status_code == 200
    assert replacement.json()["refresh"] != body2["refresh"]


def test_refresh_accepts_and_retires_pre_jti_signed_tokens():
    user = CrownUser.objects.create(
        email="legacy@x.test",
        password_hash=make_password("Passw0rd!"),
        role="teacher",
        school_id=uuid.uuid4(),
        is_active=True,
    )
    token = _legacy_refresh_token(user.id)
    assert "jti" not in decode_refresh(token).payload

    client = Client()
    response = client.post(
        "/api/auth/refresh/",
        data={"refresh": token},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["refresh"] != token

    replay = client.post(
        "/api/auth/refresh/",
        data={"refresh": token},
        content_type="application/json",
    )
    assert replay.status_code == 401


@pytest.mark.parametrize(
    "claims",
    [
        {"typ": "access"},
        {"sub": "not-a-uuid"},
        {"exp": None},
        {"iat": None},
        {"jti": None},
        {"jti": " "},
    ],
)
def test_refresh_rejects_malformed_signed_claims(claims):
    user = CrownUser.objects.create(
        email=f"malformed-{uuid.uuid4()}@x.test",
        password_hash=make_password("Passw0rd!"),
        role="staff",
        school_id=uuid.uuid4(),
        is_active=True,
    )
    token = _legacy_refresh_token(user.id, **claims)

    response = Client().post(
        "/api/auth/refresh/",
        data={"refresh": token},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert "access" not in response.json()


def test_refresh_fails_closed_when_consumption_storage_is_unavailable(monkeypatch):
    user = CrownUser.objects.create(
        email="unavailable@x.test",
        password_hash=make_password("Passw0rd!"),
        role="staff",
        school_id=uuid.uuid4(),
        is_active=True,
    )
    token = _legacy_refresh_token(user.id, jti="persistence-failure")

    def fail_create(**_kwargs):
        raise OperationalError("database unavailable")

    monkeypatch.setattr(
        "crown_api.auth_views.ConsumedCrownRefreshToken.objects.create",
        fail_create,
    )
    response = Client().post(
        "/api/auth/refresh/",
        data={"refresh": token},
        content_type="application/json",
    )

    assert response.status_code == 503
    assert response.json()["error"] == "auth_temporarily_unavailable"
    assert "access" not in response.json()
    assert "refresh" not in response.json()


def test_new_refresh_tokens_have_distinct_identifiers():
    from crown_api.jwt_utils import build_refresh_token

    first = decode_refresh(build_refresh_token(user_id=str(uuid.uuid4()))).payload
    second = decode_refresh(build_refresh_token(user_id=str(uuid.uuid4()))).payload
    assert first["jti"] != second["jti"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Refresh-token race guarantee requires PostgreSQL unique-index semantics.",
)
def test_postgresql_concurrent_refresh_consumption_succeeds_exactly_once():
    user = CrownUser.objects.create(
        email="concurrent-refresh@x.test",
        password_hash=make_password("Passw0rd!"),
        role="finance",
        school_id=uuid.uuid4(),
        is_active=True,
    )
    token = _legacy_refresh_token(user.id, jti="concurrent-refresh")
    barrier = Barrier(2)

    def refresh_once():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = Client().post(
                "/api/auth/refresh/",
                data={"refresh": token},
                content_type="application/json",
            )
            return response.status_code, response.json()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: refresh_once(), range(2)))

    successful = [body for status, body in results if status == 200]
    assert sorted(status for status, _body in results) == [200, 401]
    assert len(successful) == 1
    assert successful[0]["refresh"] != token

    replacement = Client().post(
        "/api/auth/refresh/",
        data={"refresh": successful[0]["refresh"]},
        content_type="application/json",
    )
    assert replacement.status_code == 200


def test_login_rejects_json_arrays():
    c = Client()

    r = c.post(
        "/api/auth/login/",
        data='["admin@heritage.test", "Passw0rd!"]',
        content_type="application/json",
    )

    assert r.status_code == 400
    assert r.json()["error"] == "invalid_json"


def test_me_rejects_empty_bearer_token():
    c = Client()

    r = c.get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer ")

    assert r.status_code == 401
    assert r.json()["error"] == "Unauthorized"
