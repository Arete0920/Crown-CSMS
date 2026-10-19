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


def test_blacklist_registration_and_test_database_schema():
    assert apps.is_installed("rest_framework_simplejwt.token_blacklist")
    assert settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] is True
    assert settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] is True
    tables = set(connection.introspection.table_names())
    assert OutstandingToken._meta.db_table in tables
    assert BlacklistedToken._meta.db_table in tables


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
