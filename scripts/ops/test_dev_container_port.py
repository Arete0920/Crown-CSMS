"""Regression contracts for the existing DEV App Service container port."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def test_dev_container_port_is_explicit_and_allowlisted():
    workflow = (ROOT / ".github/workflows/deploy-dev.yml").read_text()
    assert '"WEBSITES_PORT"   = "8000"' in workflow
    assert workflow.count('"WEBSITES_PORT"') == 1
    allowed = json.loads((ROOT / "tools/appsettings_allowlist.keys.json").read_text())
    assert "WEBSITES_PORT" in allowed["dev"]
    assert "WEBSITES_PORT" not in allowed["prod"]
    assert "RUN_MIGRATE" not in allowed["dev"]
    assert "RUN_MIGRATIONS" not in allowed["dev"]


def test_allowlist_integrity_is_updated():
    source = (ROOT / "tools/appsettings_allowlist.keys.json").read_bytes()
    expected = (ROOT / "tools/appsettings_allowlist.keys.json.sha256").read_text().strip()
    assert hashlib.sha256(source).hexdigest() == expected


def test_container_listens_on_expected_port():
    entrypoint = (ROOT / "entrypoint.sh").read_text()
    assert '${PORT:-8000}' in entrypoint
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "EXPOSE 8000" in dockerfile
