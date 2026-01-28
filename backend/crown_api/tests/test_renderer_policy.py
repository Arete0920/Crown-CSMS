import os
import importlib

def _reload_settings_module():
    # Crown settings are typically imported as crown_api.settings
    # Reloading lets us test env-driven settings deterministically.
    import crown_api.settings as settings
    return importlib.reload(settings)

def test_prod_uses_json_only_renderers(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "prod")
    settings = _reload_settings_module()
    renderers = settings.REST_FRAMEWORK.get("DEFAULT_RENDERER_CLASSES")
    assert renderers == ("rest_framework.renderers.JSONRenderer",)

def test_dev_allows_browsable_renderer(monkeypatch):
    monkeypatch.delenv("CROWN_ENV", raising=False)
    monkeypatch.setenv("CROWN_ENV", "dev")
    settings = _reload_settings_module()
    renderers = settings.REST_FRAMEWORK.get("DEFAULT_RENDERER_CLASSES")
    assert "rest_framework.renderers.JSONRenderer" in renderers
    assert "rest_framework.renderers.BrowsableAPIRenderer" in renderers
