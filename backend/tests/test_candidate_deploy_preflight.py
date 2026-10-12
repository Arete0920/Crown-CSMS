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
        for key in ("DJANGO_SECRET_KEY", "SECRET_KEY", "WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID"):
            env.pop(key, None)
        env.update(step["env"])
        env.update(CROWN_ENV="production", DJANGO_ENV="production", DJANGO_DEBUG="false")
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


def test_short_candidate_fixture_remains_rejected(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "candidate-validation-nonproduction-only")
    with pytest.raises(ImproperlyConfigured):
        enforce_production_secret(["manage.py", "check", "--deploy"])
