"""Source-level guardrails for explicit local-only five-module preparation.

These tests mock the process launcher. They do not certify the real SQLite
fixtures, signed-staff custody or Windows browser workflows.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def load_launcher():
    script = ROOT / "scripts" / "demo" / "start_heritage_local.py"
    spec = importlib.util.spec_from_file_location("heritage_five_module_launcher", script)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    return launcher


def local_env(state: Path):
    return {
        "DJANGO_ENV": "local",
        "CROWN_ENV": "local",
        "DJANGO_DEBUG": "true",
        "CROWN_DEMO_MODE": "false",
        "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "true",
        "VITE_LOCAL_DEMO": "1",
        "DATABASE_URL": "sqlite:///" + (state / "heritage.sqlite3").as_posix(),
    }


def test_strict_preparation_runs_existing_three_seeders_in_order(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    python = tmp_path / ".venv" / "python.exe"
    env = local_env(tmp_path)
    commands = []
    monkeypatch.setattr(launcher, "run", lambda cmd, process_env: commands.append((cmd, process_env)))

    launcher.seed_five_module_fixtures(env, python)

    manage = [str(python), str(ROOT / "backend" / "manage.py")]
    assert len(commands) == 3
    assert all(cmd[:2] == manage and process_env is env for cmd, process_env in commands)
    assert commands[0][0][2:] == ["seed_heritage_module_samples", "--fictional-local-only"]
    assert commands[1][0][2:] == [
        "shell", "--command",
        "from sandbox_demo.services import seed_local_heritage_camp; seed_local_heritage_camp()",
    ]
    assert commands[2][0][2:] == [
        "seed_fictional_sgo_intake", "--credentials-file",
        str(tmp_path / "sgo-credentials.txt"),
    ]


@pytest.mark.parametrize(("key", "value"), [
    ("DJANGO_ENV", "dev"),
    ("CROWN_ENV", "dev"),
    ("DJANGO_DEBUG", "false"),
    ("CROWN_DEMO_MODE", "true"),
    ("CROWN_SANDBOX_ALLOW_OPEN_SESSION", "false"),
    ("VITE_LOCAL_DEMO", "0"),
    ("DATABASE_URL", "postgresql://host/real-school"),
])
def test_nonlocal_or_ambiguous_configuration_blocks_all_fixture_writes(
    monkeypatch, tmp_path, key, value,
):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    commands = []
    monkeypatch.setattr(launcher, "run", lambda cmd, env: commands.append(cmd))
    env = local_env(tmp_path)
    env[key] = value

    with pytest.raises(RuntimeError, match="exact isolated Heritage local settings"):
        launcher.seed_five_module_fixtures(env, tmp_path / "python")
    assert commands == []


def test_missing_seed_command_cannot_claim_success(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    calls = []

    def failing_run(command, env):
        calls.append(command)
        raise FileNotFoundError("missing governed seeder")

    monkeypatch.setattr(launcher, "run", failing_run)
    with pytest.raises(FileNotFoundError, match="missing governed seeder"):
        launcher.seed_five_module_fixtures(local_env(tmp_path), tmp_path / "python")
    assert len(calls) == 1
    assert calls[0][-2:] == ["seed_heritage_module_samples", "--fictional-local-only"]
