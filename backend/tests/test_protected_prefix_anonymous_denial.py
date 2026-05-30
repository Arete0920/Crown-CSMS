"""
Anonymous-denial contract tests for protected API prefixes.
Priority 035 release hardening artifact.
"""

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "path",
    [
        "/api/auth/me/",
        "/api/system/whoami/",
        "/api/v1/wizards/",
        "/api/v1/reports/export/",
    ],
)
def test_protected_prefixes_reject_anonymous_requests(path):
    client = APIClient()
    response = client.get(path)
    assert response.status_code in (401, 403), f"Expected 401/403 for {path}, got {response.status_code}"
