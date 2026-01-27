"""
Pytest configuration for households spine module tests.
Override settings to disable guardian scoping (spine is school-level only).
"""
import pytest
from django.conf import settings


@pytest.fixture(scope="session", autouse=True)
def disable_guardian_scoping():
    """Override guardian scoping for spine tests."""
    # Spine module contract: school-level scoping only
    settings.HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED = False
