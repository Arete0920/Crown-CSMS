"""Fail-closed orchestration tests; subprocess mocks are not browser certification."""
import importlib.util
import inspect
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize("returncode,record,accepted", [
    (1, {"presenter_entry": "DENIED", "reason": "PRESENTER_CUSTODY_CONSUMED"}, True),
    (0, {"presenter_entry": "DENIED", "reason": "PRESENTER_CUSTODY_CONSUMED"}, False),
    (-9, {"presenter_entry": "DENIED", "reason": "PRESENTER_CUSTODY_CONSUMED"}, False),
    (1, {"presenter_entry": "DENIED", "reason": "PRESENTER_VERIFICATION_FAILED"}, False),
    (1, {"presenter_entry": "PASS", "reason": "PRESENTER_CUSTODY_CONSUMED"}, False),
    (1, None, False),
])
def test_presenter_replay_requires_specific_consumed_denial(runtime, monkeypatch, returncode, record, accepted):
    import json
    result = subprocess.CompletedProcess([], returncode, stdout="not JSON\n", stderr=json.dumps(record))
    monkeypatch.setattr(runtime.subprocess, "run", lambda *a, **kw: result)
    if accepted:
        runtime.require_consumed_presenter_denial(Path("python"), {})
    else:
        with pytest.raises(RuntimeError, match="required denial proof"):
            runtime.require_consumed_presenter_denial(Path("python"), {})


def test_verifier_never_replaces_existing_presenter_scenario(runtime):
    source = inspect.getsource(runtime.main)
    assert source.count('"seed_local_diadem_pickup"') == 1
    assert '"seed_local_diadem_pickup", "--verify"' in source
    assert '"--daycare-presenter-check"' in source
    assert "require_consumed_presenter_denial(python, env)" in source

@pytest.fixture
def runtime(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("heritage_runtime_test", root / "scripts/demo/verify_heritage_runtime.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module.launcher, "FRONTEND", tmp_path / "frontend")
    monkeypatch.setattr(module.launcher, "STATE", tmp_path / "state")
    monkeypatch.setattr(module.launcher, "npm_command", lambda: ["npm"])
    module.launcher.STATE.mkdir()
    for path in module.FIVE_MODULE_BROWSER_SOURCES:
        target = module.launcher.FRONTEND / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// Test-only source inventory placeholder.\n")
    return module

def local_env(runtime):
    return {
        "DJANGO_ENV": "local", "CROWN_ENV": "local", "DJANGO_DEBUG": "true",
        "CROWN_DEMO_MODE": "false", "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "true",
        "VITE_LOCAL_DEMO": "1",
        "DATABASE_URL": "sqlite:///" + (runtime.launcher.STATE / "heritage.sqlite3").as_posix(),
    }

def evidence(runtime):
    return {"checks": dict.fromkeys(runtime.UPSTREAM_BROWSER_CHECKS, True), "result": "FAIL"}

def test_five_module_mode_requires_real_browser_option(runtime, monkeypatch):
    monkeypatch.setattr(runtime.sys, "argv", ["verify", "--five-module"])
    with pytest.raises(SystemExit) as error:
        runtime.main()
    assert error.value.code == 2

def test_missing_module_source_stops_before_local_keys_or_servers(runtime, monkeypatch):
    monkeypatch.setattr(runtime.sys, "argv", ["verify", "--browser", "--five-module"])
    monkeypatch.setattr(runtime.launcher, "source_sha", lambda: "a" * 40)
    def missing():
        raise RuntimeError("module source missing")
    monkeypatch.setattr(runtime.launcher, "require_five_module_sources", missing)
    monkeypatch.setattr(runtime.launcher, "local_environment", lambda: pytest.fail("No key preparation"))
    monkeypatch.setattr(runtime.subprocess, "Popen", lambda *a, **kw: pytest.fail("No servers"))
    assert runtime.main() == 1
    assert '"release_certified": false' in (runtime.launcher.STATE / "rehearsal-result.json").read_text()

def test_stale_fixture_source_blocks_runtime_before_key_preparation(runtime, monkeypatch):
    monkeypatch.setattr(runtime.sys, "argv", ["verify", "--browser", "--five-module"])
    monkeypatch.setattr(runtime.launcher, "source_sha", lambda: "a" * 40)
    monkeypatch.setattr(runtime.launcher, "require_five_module_sources", lambda: None)
    (runtime.launcher.STATE / "heritage.sqlite3").write_text("test-only database placeholder")
    for marker in ("seed.complete", "relationships.complete"):
        (runtime.launcher.STATE / marker).write_text("b" * 40)
    monkeypatch.setattr(runtime.launcher, "local_environment", lambda: pytest.fail("No keys for stale fixtures"))
    assert runtime.main() == 1

@pytest.mark.parametrize("index", range(7))
def test_each_missing_browser_source_blocks_completion(runtime, monkeypatch, index):
    (runtime.launcher.FRONTEND / runtime.FIVE_MODULE_BROWSER_SOURCES[index]).unlink()
    monkeypatch.setattr(runtime.subprocess, "run", lambda *a, **kw: pytest.fail("No browser with incomplete source"))
    with pytest.raises(RuntimeError, match="browser sources are missing"):
        runtime.complete_five_module_browser_checks({}, evidence(runtime))

@pytest.mark.parametrize(("key", "value"), [
    ("DJANGO_ENV", "production"), ("CROWN_ENV", "dev"),
    ("DJANGO_DEBUG", "false"), ("CROWN_DEMO_MODE", "true"),
    ("CROWN_SANDBOX_ALLOW_OPEN_SESSION", "false"), ("VITE_LOCAL_DEMO", "0"),
    ("DATABASE_URL", "sqlite:///other.sqlite3"),
])
def test_runtime_activation_keeps_exact_local_guard(runtime, monkeypatch, key, value):
    env = local_env(runtime)
    env[key] = value
    monkeypatch.setattr(runtime.subprocess, "run", lambda *a, **kw: pytest.fail("No process outside guarded local scope"))
    with pytest.raises(RuntimeError, match="exact isolated Heritage"):
        runtime.prepare_five_module_verification(env, Path("python"))
    assert "CROWN_SGO_FICTIONAL_INTAKE_ENABLED" not in env

def test_verification_requires_existing_credentials_and_never_seeds(runtime, monkeypatch):
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw)))
    env = local_env(runtime)
    (runtime.launcher.STATE / "heritage.sqlite3").write_text("test-only database placeholder")
    with pytest.raises(RuntimeError, match="Prepare fictional SGO credentials"):
        runtime.prepare_five_module_verification(env, Path("python"))
    assert calls == []
    (runtime.launcher.STATE / "sgo-credentials.txt").write_text("fictional test placeholder")
    runtime.prepare_five_module_verification(env, Path("python"))
    assert len(calls) == 1
    assert calls[0][0][-2:] == ["five_module_demo_preflight", "--strict"]
    assert calls[0][1]["env"]["CROWN_SGO_FICTIONAL_INTAKE_ENABLED"] == "true"
    assert calls[0][1]["check"] is True
    assert "seed_fictional_sgo_intake" not in str(calls)

def test_verification_never_creates_an_absent_database(runtime, monkeypatch):
    monkeypatch.setattr(runtime.subprocess, "run", lambda *a, **kw: pytest.fail("No empty-database creation"))
    with pytest.raises(RuntimeError, match="prepared Heritage SQLite database"):
        runtime.prepare_five_module_verification(local_env(runtime), Path("python"))
    assert not (runtime.launcher.STATE / "heritage.sqlite3").exists()

@pytest.mark.parametrize("index", range(6))
def test_module_proof_cannot_be_replaced_by_other_green_checks(runtime, monkeypatch, index):
    proof = evidence(runtime)
    proof["checks"][runtime.UPSTREAM_BROWSER_CHECKS[index]] = False
    monkeypatch.setattr(runtime.subprocess, "run", lambda *a, **kw: pytest.fail("Incomplete upstream proof"))
    with pytest.raises(RuntimeError, match="upstream browser proof is incomplete"):
        runtime.complete_five_module_browser_checks({}, proof)
    assert proof["result"] == "FAIL"

def test_success_runs_care_and_sgo_once_with_required_proof_flags(runtime, monkeypatch):
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw)))
    original_env = {"CROWN_EXPECTED_FRONTEND_SHA": "a" * 40}
    proof = evidence(runtime)
    runtime.complete_five_module_browser_checks(original_env, proof)
    assert len(calls) == 2
    command, options = calls[0]
    assert command == ["npm", "run", "test:e2e", "--",
                       "tests/e2e/extended-care-local-custody.spec.ts",
                       "tests/e2e/jireh-sgo-local-intake.spec.ts",
                       "--workers=1", "--reporter=line"]
    assert calls[1] == ([
        "npm", "run", "test:e2e", "--",
        "tests/e2e/heritage-module-responsive.spec.ts",
        "tests/e2e/heritage-presenter-launcher.spec.ts",
        "--workers=1", "--reporter=line",
    ], options)
    assert options["env"]["CROWN_REQUIRE_CARE_BROWSER_PROOF"] == "1"
    assert options["env"]["CROWN_REQUIRE_SGO_BROWSER_PROOF"] == "1"
    assert options["env"]["CROWN_LOCAL_PRESENTER_E2E"] == "1"
    assert options["env"]["CROWN_REQUIRE_LOCAL_PRESENTER_PROOF"] == "1"
    assert options["env"]["CROWN_SGO_LOCAL_CREDENTIALS"] == str((runtime.launcher.STATE / "sgo-credentials.txt").resolve())
    assert options["check"] is True
    assert original_env == {"CROWN_EXPECTED_FRONTEND_SHA": "a" * 40}
    assert proof["checks"]["local_presenter_authenticated_click_path"] is True
    assert proof["checks"]["five_module_responsive_real_role_browser_audit"] is True
    assert proof["checks"]["extended_care_real_am_pm_browser_custody_and_reload"] is True
    assert proof["checks"]["jireh_sgo_independent_partners_submission_correction_and_resubmission"] is True

@pytest.mark.parametrize("failure_call", [1, 2])
def test_failed_browser_does_not_record_module_success(runtime, monkeypatch, failure_call):
    proof = evidence(runtime)
    calls = []
    def fail(command, **kwargs):
        calls.append(command)
        if len(calls) == failure_call:
            raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(runtime.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        runtime.complete_five_module_browser_checks({}, proof)
    assert "local_presenter_authenticated_click_path" not in proof["checks"]
    assert "five_module_responsive_real_role_browser_audit" not in proof["checks"]
    assert "extended_care_real_am_pm_browser_custody_and_reload" not in proof["checks"]
    assert "jireh_sgo_independent_partners_submission_correction_and_resubmission" not in proof["checks"]
