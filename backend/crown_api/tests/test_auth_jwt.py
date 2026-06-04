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
