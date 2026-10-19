"""Verify that configured refresh-token rotation actually revokes the old token.

This uses a fictional local user and never logs a bearer or refresh credential.
"""

import pytest
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


pytestmark = pytest.mark.django_db
requires_revocation = pytest.mark.skipif(
    not settings.CROWN_SIMPLEJWT_BLACKLIST_ENABLED,
    reason="Blacklist integration requires the explicitly enabled migrated test environment.",
)


@pytest.mark.skipif(
    settings.CROWN_SIMPLEJWT_BLACKLIST_ENABLED,
    reason="Default-disabled runtime contract applies only before activation.",
)
def test_default_disabled_mode_retains_stock_refresh_serializer():
    from crown_api.api_v1_urls import RateLimitedTokenRefreshView
    from rest_framework_simplejwt.serializers import TokenRefreshSerializer

    assert not apps.is_installed("rest_framework_simplejwt.token_blacklist")
    assert RateLimitedTokenRefreshView.serializer_class is TokenRefreshSerializer


@requires_revocation
def test_blacklist_registration_and_test_database_schema():
    assert apps.is_installed("rest_framework_simplejwt.token_blacklist")
    assert settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] is True
    assert settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] is True
    tables = set(connection.introspection.table_names())
    assert OutstandingToken._meta.db_table in tables
    assert BlacklistedToken._meta.db_table in tables


@requires_revocation
def test_old_refresh_cannot_be_reused_after_successful_rotation():
    cache.clear()
    user = get_user_model().objects.create_user(
        username="fictional-refresh-rotation-user",
        email="fictional-refresh-rotation-user@example.invalid",
        password=None,
        is_active=True,
    )
    old_refresh = str(RefreshToken.for_user(user))
    client = APIClient()

    def refresh(value):
        return client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": value},
            format="json",
            REMOTE_ADDR="203.0.113.45",
        )

    rotated = refresh(old_refresh)
    assert rotated.status_code == 200
    assert rotated.data.get("access")
    replacement = rotated.data.get("refresh")
    assert isinstance(replacement, str)
    assert replacement != old_refresh

    # The consumed token is rejected, rather than silently reusable.
    replay = refresh(old_refresh)
    assert replay.status_code == 401
    assert replay.data.get("code") != "rate_limited"

    # The returned replacement token remains valid for exactly the next rotation.
    second = refresh(replacement)
    assert second.status_code == 200
    assert second.data.get("refresh")
    assert BlacklistedToken.objects.filter(token__user=user).count() >= 2


@requires_revocation
@pytest.mark.django_db(transaction=True)
def test_concurrent_refresh_consumes_token_only_once():
    """Real PostgreSQL workers cannot both rotate one refresh token."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import connections

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-locking contract")

    user = get_user_model().objects.create_user(
        username="fictional-parallel-refresh",
        email="fictional-parallel-refresh@example.invalid",
        password=None,
        is_active=True,
    )
    original = str(RefreshToken.for_user(user))
    barrier = Barrier(2)

    def call_refresh(_):
        connections.close_all()
        try:
            client = APIClient()
            barrier.wait(timeout=15)
            result = client.post(
                "/api/v1/auth/token/refresh/",
                {"refresh": original},
                format="json",
                REMOTE_ADDR="203.0.113.78",
            )
            return result.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(call_refresh, range(2)))

    assert statuses == [200, 401]
    assert BlacklistedToken.objects.filter(token__user=user).count() == 1


@requires_revocation
def test_blacklist_database_failure_fails_closed():
    """A failed blacklist DB operation must not mint an access token."""
    from unittest.mock import patch
    from django.db import DatabaseError

    cache.clear()
    with patch(
        "crown_api.refresh_rotation.SerializedTokenRefreshSerializer.validate",
        side_effect=DatabaseError("synthetic unavailable database"),
    ):
        response = APIClient().post(
            "/api/v1/auth/token/refresh/",
            {"refresh": "invalid-synthetic-token"},
            format="json",
            REMOTE_ADDR="203.0.113.79",
        )
    assert response.status_code == 503
    assert response.data["code"] == "auth_temporarily_unavailable"
    assert response["Retry-After"] == "60"
    assert "access" not in response.data
