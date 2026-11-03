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
    assert env["CROWN_SGO_FICTIONAL_INTAKE_ENABLED"] == "true"
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
    assert "CROWN_SGO_FICTIONAL_INTAKE_ENABLED" not in env


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


def test_explicit_five_module_launch_must_complete_strict_audit_before_servers(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    monkeypatch.setattr(launcher.sys, "argv", ["start_heritage_local.py", "--five-module-demo"])
    monkeypatch.setattr(launcher, "available_ports", lambda: None)
    monkeypatch.setattr(launcher, "npm_command", lambda: ["npm"])
    env = local_env(tmp_path)
    python = tmp_path / "python"
    monkeypatch.setattr(launcher, "local_environment", lambda: env)
    monkeypatch.setattr(launcher, "prepare", lambda *args: python)
    calls = []
    def seed(process_env, executable):
        calls.append(("seed", executable))
        process_env["CROWN_SGO_FICTIONAL_INTAKE_ENABLED"] = "true"
    def audit(command, process_env):
        calls.append(("audit", command[-2:]))
        raise RuntimeError("synthetic audit failure")
    monkeypatch.setattr(launcher, "seed_five_module_fixtures", seed)
    monkeypatch.setattr(launcher, "run", audit)
    def forbid_server(*args, **kwargs):
        pytest.fail("No server may launch before strict five-module audit passes")
    monkeypatch.setattr(launcher.subprocess, "Popen", forbid_server)
    assert launcher.main() == 1
    assert calls == [("seed", python), ("audit", ["five_module_demo_preflight", "--strict"])]


def test_default_prepare_does_not_activate_five_module_fixtures(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher.sys, "argv", ["start_heritage_local.py", "--prepare-only"])
    monkeypatch.setattr(launcher, "available_ports", lambda: None)
    monkeypatch.setattr(launcher, "npm_command", lambda: ["npm"])
    env = local_env(tmp_path)
    monkeypatch.setattr(launcher, "local_environment", lambda: env)
    monkeypatch.setattr(launcher, "prepare", lambda *args: tmp_path / "python")
    monkeypatch.setattr(launcher, "seed_five_module_fixtures",
                        lambda *args: pytest.fail("Default launcher must not provision five-module fixtures"))
    assert launcher.main() == 0
    assert "CROWN_SGO_FICTIONAL_INTAKE_ENABLED" not in env

def test_successful_opt_in_launch_preserves_strict_sequence(monkeypatch, tmp_path):
    """Source-only launch-order proof; does not claim real browser acceptance."""
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    monkeypatch.setattr(
        launcher.sys, "argv",
        ["start_heritage_local.py", "--five-module-demo", "--no-browser"],
    )
    monkeypatch.setattr(launcher, "available_ports", lambda: None)
    monkeypatch.setattr(launcher, "npm_command", lambda: ["npm"])
    monkeypatch.setattr(launcher, "preview_command", lambda: ["vite", "preview"])
    env = local_env(tmp_path)
    python = tmp_path / "python"
    monkeypatch.setattr(launcher, "local_environment", lambda: env)
    monkeypatch.setattr(launcher, "prepare", lambda *args: python)
    calls = []

    def seed(process_env, executable):
        assert process_env is env
        assert executable == python
        assert "CROWN_SGO_FICTIONAL_INTAKE_ENABLED" not in env
        process_env["CROWN_SGO_FICTIONAL_INTAKE_ENABLED"] = "true"
        calls.append("seed")

    def audit(command, process_env):
        assert process_env is env
        assert command[-2:] == ["five_module_demo_preflight", "--strict"]
        calls.append("strict")

    class FakeServer:
        def __init__(self, name):
            self.name = name
        def poll(self):
            return None
        def terminate(self):
            calls.append("stop-" + self.name)
        def wait(self, timeout=None):
            return 0

    def spawn(command, *, cwd, env, stdout, stderr):
        assert env["CROWN_SGO_FICTIONAL_INTAKE_ENABLED"] == "true"
        if "heritage_runserver" in command:
            assert command[-2:] == ["127.0.0.1:8000", "--noreload"]
            calls.append("backend")
            return FakeServer("backend")
        assert command == ["vite", "preview"]
        calls.append("frontend")
        return FakeServer("frontend")

    def ready(url, process, **kwargs):
        assert process.name in ("backend", "frontend")
        assert url.startswith("http://127.0.0.1:") or url.startswith("http://localhost:")
        calls.append("ready-" + process.name)

    monkeypatch.setattr(launcher, "seed_five_module_fixtures", seed)
    monkeypatch.setattr(launcher, "run", audit)
    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    monkeypatch.setattr(launcher, "wait_ready", ready)
    monkeypatch.setattr(launcher.time, "sleep", lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    assert launcher.main() == 0
    assert calls == [
        "seed", "strict", "backend", "frontend",
        "ready-backend", "ready-frontend", "stop-frontend", "stop-backend",
    ]
