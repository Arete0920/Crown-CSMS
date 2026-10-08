"""Repository security contract for external tool integrations."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools" / "ci" / "verify_tool_integration_security.py"


def test_external_tool_integration_policy_fails_closed():
    result = subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Tool integration security gate PASSED" in result.stdout


def test_repository_policy_covers_nested_container_paths():
    """Nested Docker/compose changes must trigger and enter the config-security gate."""
    workflow = (ROOT / ".github" / "workflows" / "repository-policy.yml").read_text(encoding="utf-8")
    required = (
        '"**/Dockerfile*"',
        '"**/docker-compose*.yml"',
        '"**/docker-compose*.yaml"',
        "'**/Dockerfile*'",
        "'**/docker-compose*.yml'",
        "'**/docker-compose*.yaml'",
    )
    missing = [pattern for pattern in required if pattern not in workflow]
    assert not missing, f"repository policy misses nested container coverage: {missing}"


def _load_checker_module():
    spec = importlib.util.spec_from_file_location("tool_integration_security_checker", CHECKER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_external_tool_registry_rejects_weak_entries():
    checker = _load_checker_module()
    base = {
        "id": "crown.example",
        "status": "approved",
        "owner": "Security",
        "transport": "remote",
        "version": "1.2.3",
        "artifact_digest": "sha256:" + ("a" * 64),
        "tools": ["crown.example.read.v1"],
        "permissions": ["records.read"],
        "data_classifications": ["internal"],
        "egress_hosts": ["api.example.test"],
        "config_paths": ["config/security/example.json"],
        "human_approval_for_writes": True,
        "auto_run": False,
        "reviewed_at": "2026-10-07",
        "disable_procedure": "Disable the registry entry and remove runtime configuration.",
    }

    bad_cases = (
        ({**base, "version": "latest"}, "version must be exact"),
        ({**base, "artifact_digest": "sha256:not-a-digest"}, "artifact_digest"),
        ({**base, "egress_hosts": ["*.example.test"]}, "exact hostnames"),
        ({
            **base,
            "permissions": ["records.write"],
            "human_approval_for_writes": False,
        }, "write-capable permission requires human approval"),
        ({
            **base,
            "permissions": ["records.write"],
            "auto_run": True,
        }, "write-capable permission cannot auto-run"),
        ({
            **base,
            "data_classifications": ["student-education-record"],
            "auto_run": True,
        }, "protected-data tools cannot auto-run"),
        ({**base, "reviewed_at": "2999-01-01"}, "reviewed_at cannot be in the future"),
    )

    for entry, expected in bad_cases:
        errors = checker._validate_entry(entry, set(), set())
        assert any(expected in error for error in errors), (expected, errors)
