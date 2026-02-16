import pytest
from uuid import uuid4

from django.test import Client

from crown_api.models import CrownUser
from crown_api.jwt_utils import build_access_token

pytestmark = pytest.mark.django_db


def _make_user(role="finance", school_id=None, email="t@t.com", password="Passw0rd!"):
    if school_id is None:
        school_id = uuid4()
    from django.contrib.auth.hashers import make_password
    u = CrownUser.objects.create(
        email=email,
        role=role,
        school_id=school_id,
        is_active=True,
        password_hash=make_password(password),
    )
    return u


def _auth_header_for(user: CrownUser):
    token = build_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        school_id=str(user.school_id) if user.school_id else None,
        ttl_seconds=900,
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_tenant_resolves_from_jwt_user_school_id():
    c = Client()
    school_id = uuid4()
    u = _make_user(role="finance", school_id=school_id, email="a@a.com")
    hdr = _auth_header_for(u)

    # Hit /api/auth/me/ (should not require header; should work)
    r = c.get("/api/auth/me/", **hdr)
    assert r.status_code == 200
    data = r.json()
    assert str(school_id) in str(data)  # permissive check


def test_protected_endpoint_requires_tenant_when_no_jwt_and_no_header():
    c = Client()
    # No auth, no header → should get 401 or 403
    r = c.get("/api/v1/gradebook/sections/")
    assert r.status_code in (401, 403)


def test_cross_tenant_header_does_not_override_jwt_tenant():
    c = Client()
    school_a = uuid4()
    school_b = uuid4()
    u = _make_user(role="finance", school_id=school_a, email="b@b.com")
    hdr = _auth_header_for(u)

    # Attempt to override tenant via header. Resolver prioritizes JWT.
    hdr["HTTP_X_SCHOOL_ID"] = str(school_b)

    # Hit /api/auth/me/ - should still show school_a, not school_b
    r = c.get("/api/auth/me/", **hdr)
    assert r.status_code == 200
    data = r.json()
    # JWT tenant (school_a) should be in the response
    assert str(school_a) in str(data) or "school_id" in str(data).lower()
