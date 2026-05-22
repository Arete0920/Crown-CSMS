"""
Wave 3 P1-2: Back-compat alias auth parity tests.

These tests verify that /api/dashboards/* behaves the same as
/api/v1/dashboards/* for authentication and tenant enforcement.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

User = get_user_model()


@pytest.fixture()
def school(db):
    return School.objects.create(name="Alias Parity School")


@pytest.fixture()
def user(db, school):
    return User.objects.create_user(
        username="alias_parity_user",
        email="alias@test.com",
        password="pw",
        school_id=school.id,
    )


@pytest.fixture()
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _assert_status_parity(client, canonical_path, alias_path, **headers):
    canonical = client.get(canonical_path, **headers)
    alias = client.get(alias_path, **headers)
    assert canonical.status_code == alias.status_code, (
        f"status mismatch: {canonical_path}={canonical.status_code}, "
        f"{alias_path}={alias.status_code}"
    )
    return canonical, alias


@pytest.mark.django_db
def test_canonical_and_alias_dashboard_me_require_auth(school):
    client = APIClient()
    canonical, alias = _assert_status_parity(
        client,
        "/api/v1/dashboards/me/",
        "/api/dashboards/me/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert canonical.status_code in (401, 403)


@pytest.mark.django_db
def test_canonical_and_alias_dashboard_summary_missing_tenant_header(auth_client):
    canonical, alias = _assert_status_parity(
        auth_client,
        "/api/v1/dashboards/summary/",
        "/api/dashboards/summary/",
    )
    assert canonical.status_code == 400


@pytest.mark.django_db
def test_canonical_and_alias_dashboard_summary_nonexistent_tenant(auth_client):
    canonical, alias = _assert_status_parity(
        auth_client,
        "/api/v1/dashboards/summary/",
        "/api/dashboards/summary/",
        HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000000",
    )
    assert canonical.status_code == 404


@pytest.mark.django_db
def test_canonical_and_alias_dashboard_summary_happy_path(auth_client, school):
    canonical, alias = _assert_status_parity(
        auth_client,
        "/api/v1/dashboards/summary/",
        "/api/dashboards/summary/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert canonical.status_code == 200
    assert canonical.json().get("school_id") == str(school.id)
    assert alias.json().get("school_id") == str(school.id)


@pytest.mark.django_db
def test_canonical_and_alias_admissions_funnel_missing_tenant_header(auth_client):
    canonical, alias = _assert_status_parity(
        auth_client,
        "/api/v1/dashboards/admissions/funnel/",
        "/api/dashboards/admissions/funnel/",
    )
    assert canonical.status_code == 400
