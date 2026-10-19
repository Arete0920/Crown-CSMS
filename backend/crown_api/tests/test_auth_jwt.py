# backend/crown_api/tests/test_auth_jwt.py
import uuid
import pytest
from django.test import Client
from django.contrib.auth.hashers import make_password

from crown_api.auth_models import CrownUser


pytestmark = pytest.mark.django_db


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


def test_refresh_issues_new_access():
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
    assert "refresh" in body2 and len(body2["refresh"]) > 20
    assert body2["refresh"] != refresh
    replay = c.post(
        "/api/auth/refresh/", data={"refresh": refresh},
        content_type="application/json",
    )
    assert replay.status_code == 401
    rotated = c.post(
        "/api/auth/refresh/", data={"refresh": body2["refresh"]},
        content_type="application/json",
    )
    assert rotated.status_code == 200

    # new access works on /me
    r = c.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {body2['access']}")
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "finance"


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


def test_refresh_tokens_issued_in_same_second_are_distinct():
    from crown_api.jwt_utils import build_refresh_token

    user_id = str(uuid.uuid4())
    assert build_refresh_token(user_id=user_id) != build_refresh_token(user_id=user_id)


def test_signed_legacy_refresh_without_expiry_is_rejected():
    from django.conf import settings
    from crown_api.jwt_utils import encode_jwt

    user = CrownUser.objects.create(
        email="no-expiry@example.invalid", password_hash=make_password("Valid-Passphrase!"),
        role="teacher", school_id=uuid.uuid4(), is_active=True,
    )
    malformed = encode_jwt(
        {"typ": "refresh", "sub": str(user.pk)},
        secret=settings.SECRET_KEY + "|refresh",
    )
    result = Client().post(
        "/api/auth/refresh/", data={"refresh": malformed},
        content_type="application/json", REMOTE_ADDR="203.0.113.81",
    )
    assert result.status_code == 401


def test_legacy_refresh_database_outage_never_issues_access():
    from unittest.mock import patch
    from django.db import DatabaseError
    from crown_api.jwt_utils import build_refresh_token

    user = CrownUser.objects.create(
        email="db-outage@example.invalid", password_hash=make_password("Valid-Passphrase!"),
        role="staff", school_id=uuid.uuid4(), is_active=True,
    )
    token = build_refresh_token(user_id=str(user.pk))
    with patch(
        "crown_api.auth_views.LegacyRefreshConsumption.objects.create",
        side_effect=DatabaseError("synthetic read-only database outage"),
    ):
        result = Client().post(
            "/api/auth/refresh/", data={"refresh": token},
            content_type="application/json", REMOTE_ADDR="203.0.113.82",
        )
    assert result.status_code == 503
    assert result.json()["error"] == "auth_temporarily_unavailable"


@pytest.mark.django_db(transaction=True)
def test_concurrent_legacy_refresh_allows_exactly_one_redemption():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, connections
    from crown_api.auth_models import LegacyRefreshConsumption
    from crown_api.jwt_utils import build_refresh_token

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL unique-key concurrency contract")
    user = CrownUser.objects.create(
        email="parallel-refresh@example.invalid",
        password_hash=make_password("Valid-Passphrase!"),
        role="staff", school_id=uuid.uuid4(), is_active=True,
    )
    token = build_refresh_token(user_id=str(user.pk))
    barrier = Barrier(2)

    def redeem(_):
        connections.close_all()
        try:
            barrier.wait(timeout=15)
            return Client().post(
                "/api/auth/refresh/", data={"refresh": token},
                content_type="application/json", REMOTE_ADDR="203.0.113.83",
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = sorted(pool.map(redeem, range(2)))
    assert results == [200, 401]
    assert LegacyRefreshConsumption.objects.filter(user=user).count() == 1


def test_legacy_refresh_rechecks_current_user_under_database_lock():
    from unittest.mock import patch
    from crown_api.jwt_utils import build_refresh_token

    user = CrownUser.objects.create(
        email="locked-refresh@example.invalid",
        password_hash=make_password("Valid-Passphrase!"),
        role="staff", school_id=uuid.uuid4(), is_active=True,
    )
    token = build_refresh_token(user_id=str(user.pk))
    with patch("crown_api.auth_views.CrownUser.objects.select_for_update") as selected, \
            patch("crown_api.auth_views.LegacyRefreshConsumption.objects.create") as consumed:
        selected.return_value.get.side_effect = CrownUser.DoesNotExist
        result = Client().post(
            "/api/auth/refresh/", data={"refresh": token},
            content_type="application/json", REMOTE_ADDR="203.0.113.84",
        )
    assert result.status_code == 401
    assert result.json()["error"] == "invalid_refresh"
    consumed.assert_not_called()


def test_legacy_default_disabled_mode_does_not_require_consumption_table():
    from django.test import override_settings
    from unittest.mock import patch
    from crown_api.jwt_utils import build_refresh_token

    user = CrownUser.objects.create(
        email="disabled-ledger@example.invalid", password_hash=make_password("Valid-Passphrase!"),
        role="staff", school_id=uuid.uuid4(), is_active=True,
    )
    signed = build_refresh_token(user_id=str(user.pk))
    with override_settings(CROWN_LEGACY_REFRESH_ONE_USE_ENABLED=False), patch(
        "crown_api.auth_views.LegacyRefreshConsumption.objects.create",
        side_effect=AssertionError("disabled mode must not touch consumption schema"),
    ):
        first = Client().post("/api/auth/refresh/", data={"refresh": signed},
                              content_type="application/json")
        second = Client().post("/api/auth/refresh/", data={"refresh": signed},
                               content_type="application/json")
    assert first.status_code == second.status_code == 200
    assert "access" in first.json()
    assert "refresh" not in first.json()
