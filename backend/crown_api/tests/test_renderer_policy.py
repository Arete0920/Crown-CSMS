"""Verify environment-specific renderer policy without mutating process-global settings."""

import json
import os
from pathlib import Path
import subprocess
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[2]
STRONG_TEST_SECRET = "renderer-fixture-strong-nonproduction-value-" + ("Ab7!" * 16)


def _renderer_classes(environment: str) -> tuple[str, ...]:
    """Import real Django settings in a clean process without a database connection."""
    env = os.environ.copy()
    for name in (
        "CROWN_ENV",
        "DJANGO_ENV",
        "ENVIRONMENT",
        "AZURE_ENVIRONMENT",
        "APP_ENV",
        "WEBSITE_HOSTNAME",
        "WEBSITE_INSTANCE_ID",
        "CROWN_DEPLOY_SECURITY",
        "CROWN_DEMO_MODE",
        "DATABASE_URL",
        "DJANGO_DEBUG",
        "DEBUG",
        "DJANGO_SECRET_KEY",
        "SECRET_KEY",
    ):
        env.pop(name, None)
    hosted = environment == "prod"
    env.update(
        DJANGO_SETTINGS_MODULE="crown_api.settings",
        CROWN_ENV=environment,
        DJANGO_ENV="production" if hosted else "dev",
        DJANGO_DEBUG="false",
        CROWN_DEMO_MODE="false",
        DJANGO_SECRET_KEY=STRONG_TEST_SECRET,
        DATABASE_URL=(
            "postgresql://db.example.invalid/crown"
            if hosted
            else "sqlite:///./renderer-test.sqlite3"
        ),
    )
    code = (
        "import json; import crown_api.settings as settings; "
        "print(json.dumps(settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return tuple(json.loads(result.stdout.strip().splitlines()[-1]))


def test_prod_uses_json_only_renderers():
    assert _renderer_classes("prod") == ("rest_framework.renderers.JSONRenderer",)


def test_dev_allows_browsable_renderer():
    renderers = _renderer_classes("dev")
    assert "rest_framework.renderers.JSONRenderer" in renderers
    assert "rest_framework.renderers.BrowsableAPIRenderer" in renderers
