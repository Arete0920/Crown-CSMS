"""Source-level guardrails for explicit local-only five-module preparation.

These tests mock the process launcher. They do not certify the real SQLite
fixtures, signed-staff custody or Windows browser workflows.
"""
from __future__ import annotations

import importlib.util
import inspect
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

def test_sgo_seed_stays_opt_in_and_runs_once():
    """Guard cross-PR launcher integration against double credential rotation.
    #616 currently seeds SGO in ordinary prepare, while #615 seeds it in the
    explicit five-module path. The integrated launcher must preserve only the
    opt-in invocation and never enable SGO from ordinary local_environment.
    """
    launcher = load_launcher()
    default_environment = inspect.getsource(launcher.local_environment)
    normal_preparation = inspect.getsource(launcher.prepare)
    opt_in_preparation = inspect.getsource(launcher.seed_five_module_fixtures)
    # Do not enable partner-family/processor endpoints in the basic demo.
    assert "CROWN_SGO_FICTIONAL_INTAKE_ENABLED" not in default_environment
    # Do not call a password-rotating SGO seeder during ordinary preparation.
    assert "seed_fictional_sgo_intake" not in normal_preparation
    # One and only one seeder invocation in explicitly guarded preparation.
    assert opt_in_preparation.count('"seed_fictional_sgo_intake"') == 1

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
    assert commands[0][0][2:] == ["seed_heritage_module_samples", "--fictional-local-only",
                                 "--enable-fictional-care-entitlements"]
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
    assert calls[0][-3:] == ["seed_heritage_module_samples", "--fictional-local-only",
                           "--enable-fictional-care-entitlements"]

def test_missing_five_module_source_fails_before_install_or_database_mutation(monkeypatch, tmp_path, capsys):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher.sys, "argv", ["start_heritage_local.py", "--prepare-only", "--five-module-preflight"])
    monkeypatch.setattr(launcher, "local_environment",
                        lambda: pytest.fail("Missing source must stop before creating local credentials"))
    monkeypatch.setattr(
        launcher, "prepare",
        lambda *_: pytest.fail("Missing source must stop before installs and migrations"),
    )
    assert launcher.main() == 1
    error = capsys.readouterr().err
    assert "Five-module demonstration source is incomplete" in error
    assert "seed_heritage_module_samples.py" in error
    assert "seed_fictional_sgo_intake.py" in error

def test_source_prerequisite_rejects_camp_placeholder_but_accepts_declared_fixture(tmp_path):
    launcher = load_launcher()
    paths = [
        "frontend/dashboards/scripts/heritage-daycare-presenter.mjs",
        "backend/sandbox_demo/management/commands/seed_local_diadem_pickup.py",
        "backend/sandbox_demo/management/commands/seed_heritage_module_samples.py",
        "backend/crown_api/management/commands/seed_fictional_sgo_intake.py",
        "backend/sandbox_demo/management/commands/five_module_demo_preflight.py",
        "backend/sandbox_demo/services.py",
    ]
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def other(): pass\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="seed_local_heritage_camp"):
        launcher.require_five_module_sources(tmp_path)
    (tmp_path / "backend/sandbox_demo/services.py").write_text(
        "def seed_local_heritage_camp():\n    return None\n", encoding="utf-8"
    )
    launcher.require_five_module_sources(tmp_path)

def test_explicit_five_module_launch_must_complete_strict_audit_before_servers(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    monkeypatch.setattr(launcher.sys, "argv", ["start_heritage_local.py", "--five-module-demo"])
    monkeypatch.setattr(launcher, "available_ports", lambda: None)
    monkeypatch.setattr(launcher, "require_five_module_sources", lambda: None)
    monkeypatch.setattr(launcher, "source_sha", lambda: "a" * 40)
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

@pytest.mark.parametrize(("mode", "stale_marker"), [
    (["--five-module-demo"], "seed.complete"),
    (["--five-module-demo"], "relationships.complete"),
    (["--prepare-only", "--five-module-preflight"], "seed.complete"),
    (["--prepare-only", "--five-module-preflight"], "relationships.complete"),
])
def test_opt_in_rejects_stale_marker_before_local_setup(
    monkeypatch, tmp_path, capsys, mode, stale_marker,
):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    (tmp_path / "heritage.sqlite3").write_bytes(b"fictional-test-only")
    for name in ("seed.complete", "relationships.complete"):
        (tmp_path / name).write_text("a" * 40, encoding="utf-8")
    (tmp_path / stale_marker).write_text("b" * 40, encoding="utf-8")
    monkeypatch.setattr(launcher.sys, "argv", ["start_heritage_local.py", *mode])
    monkeypatch.setattr(launcher, "source_sha", lambda: "a" * 40)
    monkeypatch.setattr(launcher, "require_five_module_sources", lambda: None)
    monkeypatch.setattr(launcher, "local_environment", lambda: pytest.fail("No secrets or installs on stale data"))
    assert launcher.main() == 1
    assert "another source revision" in capsys.readouterr().err

@pytest.mark.parametrize("missing", ["seed.complete", "relationships.complete"])
def test_existing_db_refuses_incomplete_provenance(monkeypatch, tmp_path, missing):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    (tmp_path / "heritage.sqlite3").write_bytes(b"fictional-test-only")
    existing = "relationships.complete" if missing == "seed.complete" else "seed.complete"
    (tmp_path / existing).write_text("a" * 40, encoding="utf-8")
    with pytest.raises(RuntimeError, match="incomplete seed markers"):
        launcher.require_fresh_five_module_source("a" * 40)

def test_marker_without_db_refused(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    (tmp_path / "seed.complete").write_text("a" * 40, encoding="utf-8")
    with pytest.raises(RuntimeError, match="without local database"):
        launcher.require_fresh_five_module_source("a" * 40)

def test_fresh_revision_or_matching_completed_markers_allowed(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    assert launcher.require_fresh_five_module_source("a" * 40) is None
    (tmp_path / "heritage.sqlite3").write_bytes(b"fictional-test-only")
    for name in ("seed.complete", "relationships.complete"):
        (tmp_path / name).write_text("a" * 40 + "\n", encoding="utf-8")
    assert launcher.require_fresh_five_module_source("a" * 40) is None

def test_malformed_source_sha_refused(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    with pytest.raises(RuntimeError, match="exact source SHA"):
        launcher.require_fresh_five_module_source("unknown")

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
    monkeypatch.setattr(launcher.sys, "argv", ["start_heritage_local.py", "--five-module-demo", "--no-browser"])
    monkeypatch.setattr(launcher, "available_ports", lambda: None)
    monkeypatch.setattr(launcher, "require_five_module_sources", lambda: None)
    monkeypatch.setattr(launcher, "source_sha", lambda: "a" * 40)
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
    assert calls == ["seed", "strict", "backend", "frontend",
                     "ready-backend", "ready-frontend", "stop-frontend", "stop-backend"]

def test_archive_identity_cannot_be_replaced_by_parent_git(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    (tmp_path / "HERITAGE_SOURCE_COMMIT.txt").write_text("a" * 40)
    monkeypatch.setattr(launcher.subprocess, "check_output", lambda *a, **kw: pytest.fail("Parent Git is not archive provenance"))
    assert launcher.source_sha() == "a" * 40
