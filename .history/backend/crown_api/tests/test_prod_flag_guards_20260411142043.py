"""
Stage 3 – Tenant & Security Seal
==================================
Production flag guard unit tests.

These tests prove the _assert_not_prod_true() helper logic directly,
without reloading the settings module with env vars (which is brittle).
"""

import importlib

import pytest


def test_prod_guard_blocks_cors_allow_all_origins(monkeypatch):
    s = importlib.import_module("crown_api.settings")

    # Simulate a production environment (DEBUG=False)
    monkeypatch.setattr(s, "DEBUG", False, raising=False)

    with pytest.raises(RuntimeError) as exc:
        s._assert_not_prod_true("CORS_ALLOW_ALL_ORIGINS", True)

    assert "CORS_ALLOW_ALL_ORIGINS cannot be enabled in production" in str(exc.value)


def test_prod_guard_blocks_demo_mode(monkeypatch):
    s = importlib.import_module("crown_api.settings")

    monkeypatch.setattr(s, "DEBUG", False, raising=False)

    with pytest.raises(RuntimeError) as exc:
        s._assert_not_prod_true("CROWN_DEMO_MODE", True)

    assert "CROWN_DEMO_MODE cannot be enabled in production" in str(exc.value)


def test_prod_guard_allows_flag_in_debug(monkeypatch):
    """Guard must not raise when DEBUG=True (dev environment)."""
    s = importlib.import_module("crown_api.settings")

    monkeypatch.setattr(s, "DEBUG", True, raising=False)

    # Should not raise
    s._assert_not_prod_true("CORS_ALLOW_ALL_ORIGINS", True)
    s._assert_not_prod_true("CROWN_DEMO_MODE", True)


def test_prod_guard_allows_false_flag_in_prod(monkeypatch):
    """Guard must not raise when the flag is False, regardless of DEBUG."""
    s = importlib.import_module("crown_api.settings")

    monkeypatch.setattr(s, "DEBUG", False, raising=False)

    # Should not raise — False flags are always safe
    s._assert_not_prod_true("CORS_ALLOW_ALL_ORIGINS", False)
    s._assert_not_prod_true("CROWN_DEMO_MODE", False)


def test_prod_guard_error_message_contains_flag_name(monkeypatch):
    """Error message must name the offending flag so operators know what to fix."""
    s = importlib.import_module("crown_api.settings")

    monkeypatch.setattr(s, "DEBUG", False, raising=False)

    with pytest.raises(RuntimeError) as exc:
        s._assert_not_prod_true("MY_DANGEROUS_FLAG", True)

    assert "MY_DANGEROUS_FLAG" in str(exc.value)


def test_resolve_debug_honors_debug_env_when_django_debug_missing(monkeypatch):
    s = importlib.import_module("crown_api.settings")

    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    monkeypatch.setenv("DEBUG", "0")

    assert s._resolve_debug(default=True) is False


def test_resolve_debug_prefers_django_debug_over_debug(monkeypatch):
    s = importlib.import_module("crown_api.settings")

    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DEBUG", "1")

    assert s._resolve_debug(default=True) is False
