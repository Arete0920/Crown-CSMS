"""Contract tests for the Heritage launcher Node.js engine guard."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_launcher():
    path = ROOT / "scripts" / "demo" / "start_heritage_local.py"
    spec = importlib.util.spec_from_file_location("heritage_local_node_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("version", "supported"),
    [
        ("v20.19.0", False),
        ("v22.12.0", False),
        ("v22.22.1", False),
        ("v22.22.2", True),
        ("v22.23.3", True),
        ("v23.0.0", False),
        ("v24.14.9", False),
        ("v24.15.0", True),
        ("v24.16.1", True),
        ("v25.0.0", False),
        ("v26.0.0", True),
        ("v27.2.1", True),
        ("v22.23.3-rc.1", False),
        ("22.22", False),
        ("not-a-version", False),
    ],
)
def test_heritage_launcher_only_accepts_dashboard_node_engines(version, supported):
    launcher = load_launcher()
    assert launcher.supported_node_runtime(version) is supported


def test_heritage_launcher_engine_contract_matches_dashboard_manifest():
    manifest = json.loads((ROOT / "frontend" / "dashboards" / "package.json").read_text(encoding="utf-8"))
    assert manifest["engines"]["node"] == "^22.22.2 || ^24.15.0 || >=26.0.0"


@pytest.mark.parametrize("version", ["v22.12.0", "v22.22.1", "v23.0.0", "v24.14.9", "v25.0.0", "broken"])
def test_npm_command_rejects_unsupported_versions_before_install(monkeypatch, tmp_path, version):
    launcher = load_launcher()
    node = str(tmp_path / "node")
    npm = str(tmp_path / "npm.js")
    monkeypatch.setattr(launcher.shutil, "which", lambda cmd: {"node": node, "npm": npm}.get(cmd))
    monkeypatch.setattr(launcher.subprocess, "check_output", lambda *args, **kwargs: version)
    with pytest.raises(RuntimeError, match="Unsupported Node.js"):
        launcher.npm_command()


@pytest.mark.parametrize("version", ["v22.22.2", "v22.23.3", "v24.15.0", "v26.0.0"])
def test_npm_command_keeps_supported_npm_cli(monkeypatch, tmp_path, version):
    launcher = load_launcher()
    node = str(tmp_path / "node")
    npm = str(tmp_path / "npm.js")
    monkeypatch.setattr(launcher.shutil, "which", lambda cmd: {"node": node, "npm": npm}.get(cmd))
    monkeypatch.setattr(launcher.subprocess, "check_output", lambda *args, **kwargs: version)
    assert launcher.npm_command() == [node, npm]


def test_npm_command_requires_node_and_npm(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setattr(launcher.shutil, "which", lambda _command: None)
    with pytest.raises(RuntimeError, match="with npm"):
        launcher.npm_command()
