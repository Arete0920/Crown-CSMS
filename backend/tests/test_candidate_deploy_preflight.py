"""Exercise the candidate preflight scripts against the hardened secret contract."""

import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml
from django.core.exceptions import ImproperlyConfigured

from crown_api.production_secret_guard import enforce_production_secret

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("workflow", ["deploy-prod.yml", "deploy-prod-dispatch.yml"])
def test_candidate_preflight_uses_fresh_strong_isolated_credentials(workflow):
    definition = yaml.safe_load((ROOT / ".github" / "workflows" / workflow).read_text())
    step = next(row for row in definition["jobs"]["candidate-verification"]["steps"]
                if row["name"] == "Preflight gate (Django deploy checks)")
    assert step["env"]["DATABASE_URL"].startswith("sqlite:")
    assert "DJANGO_SECRET_KEY" not in step["env"]
    observed = set()
    for _ in range(2):
        env = os.environ.copy()
        # This preflight runs locally on an isolated runner, not on a hosted
        # production database. Django's --deploy flag still enforces hardened
        # secret and deployment checks without falsely classifying SQLite as
        # a hosted production database.
        for key in (
            "DJANGO_SECRET_KEY", "SECRET_KEY", "CROWN_ENV", "DJANGO_ENV",
            "ENVIRONMENT", "AZURE_ENVIRONMENT", "WEBSITE_HOSTNAME",
            "WEBSITE_INSTANCE_ID", "CROWN_DEPLOY_SECURITY",
        ):
            env.pop(key, None)
        env.update(step["env"])
        env.update(DJANGO_DEBUG="false", CROWN_DEMO_MODE="false",
                   CORS_ALLOW_ALL_ORIGINS="false")
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(["bash", "-c", step["run"]], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stderr
        masked = [line.removeprefix("::add-mask::") for line in result.stdout.splitlines()
                  if line.startswith("::add-mask::")]
        assert len(masked) == 1
        assert len(masked[0]) >= 50 and len(set(masked[0])) >= 5
        observed.add(masked[0])
    assert len(observed) == 2



def test_production_marked_sqlite_preflight_is_rejected():
    """Production markers cannot reuse the isolated CI SQLite exception."""
    env = os.environ.copy()
    for key in (
        "DJANGO_ENV", "ENVIRONMENT", "AZURE_ENVIRONMENT",
        "WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "CROWN_DEPLOY_SECURITY",
    ):
        env.pop(key, None)
    env.update(
        CROWN_ENV="production",
        DATABASE_URL="sqlite:///./candidate-check.sqlite3",
        DJANGO_SECRET_KEY="StrongProductionOnlyFixtureKey-WithEntropy-123456789-Aa!",
        DJANGO_DEBUG="false",
        CROWN_DEMO_MODE="false",
    )
    result = subprocess.run(
        [sys.executable, "backend/manage.py", "check", "--deploy"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert "Hosted and staging/production database must not use SQLite." in (
        result.stdout + result.stderr
    )

def test_short_candidate_fixture_remains_rejected(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "candidate-validation-nonproduction-only")
    with pytest.raises(ImproperlyConfigured):
        enforce_production_secret(["manage.py", "check", "--deploy"])
