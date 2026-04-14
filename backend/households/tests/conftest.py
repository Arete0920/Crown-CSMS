"""
Pytest configuration for households spine module tests.
Override settings to disable guardian scoping (spine is school-level only).
"""
import pytest


@pytest.fixture(autouse=True)
def disable_guardian_scoping(settings):
    """Disable guardian scoping for households package tests only."""
    settings.HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED = False
