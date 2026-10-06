import os
from pathlib import Path
import subprocess
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_crown_env_production_reaches_final_hardening_guard():
    env = os.environ.copy()
    for name in ("DJANGO_ENV", "ENVIRONMENT", "AZURE_ENVIRONMENT", "WEBSITE_HOSTNAME"):
        env.pop(name, None)

    env.update(
        {
            "CROWN_ENV": "production",
            "DJANGO_DEBUG": "true",
            "DEBUG": "false",
            "DJANGO_SECRET_KEY": "production-test-secret-" + ("x" * 64),
            "CORS_ALLOW_ALL_ORIGINS": "0",
            "CROWN_DEMO_MODE": "0",
        }
    )

    result = subprocess.run(
        [sys.executable, "-c", "import crown_api.settings"],
        cwd=BACKEND_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode != 0
    assert "DEBUG=True is forbidden in production." in output
