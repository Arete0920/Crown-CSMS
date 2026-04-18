"""
Pytest configuration for households spine module tests.
Disable guardian scoping for most households tests, but allow explicit
contract tests to opt in to real guardian scoping behavior.
"""
import pytest


@pytest.fixture(autouse=True)
def disable_guardian_scoping(settings, request):
    """Default spine behavior is school-level only unless a test opts in."""
    if request.node.fspath and request.node.fspath.basename == "test_guardian_scoping.py":
        return
    settings.HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED = False
