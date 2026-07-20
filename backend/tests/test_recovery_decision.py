from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/recovery/recovery_decision.py"
SPEC = importlib.util.spec_from_file_location("recovery_decision", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_healthy_runtime_skips_rollback() -> None:
    row = MODULE.evaluate("healthy", False, False)
    assert row.decision == "skip_application_rollback"
    assert row.result == "PASS"
    assert row.production_mutation_performed is False


def test_unhealthy_runtime_uses_immutable_image() -> None:
    row = MODULE.evaluate("unhealthy", True, False)
    assert row.decision == "restore_immutable_last_known_good_image"
    assert row.manual_intervention is False


def test_unavailable_runtime_uses_restore_fallback_when_image_missing() -> None:
    row = MODULE.evaluate("unavailable", False, True)
    assert row.result == "PASS_WITH_MANUAL_CONTROL"
    assert row.manual_intervention is True
    assert row.database_restore_required is False


def test_missing_all_recovery_controls_fails_closed() -> None:
    row = MODULE.evaluate("unhealthy", False, False)
    assert row.result == "FAIL"
    assert row.database_restore_required is True


def test_invalid_health_is_rejected() -> None:
    try:
        MODULE.evaluate("unknown", True, True)
    except ValueError as exc:
        assert "unsupported runtime health" in str(exc)
    else:
        raise AssertionError("invalid runtime health was accepted")


def test_sha_validation_requires_lowercase_full_sha() -> None:
    MODULE.validate_sha("a" * 40, "candidate")
    for value in ("a" * 39, "A" * 40, "not-a-sha"):
        try:
            MODULE.validate_sha(value, "candidate")
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid SHA accepted: {value}")


def test_cli_packet_is_bound_to_repository_sha(tmp_path, monkeypatch) -> None:
    output = tmp_path / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "recovery_decision.py",
            "--repository-sha",
            "a" * 40,
            "--failed-candidate-sha",
            "1" * 40,
            "--last-known-good-sha",
            "2" * 40,
            "--runtime-health",
            "healthy",
            "--no-immutable-image-available",
            "--no-restore-evidence-available",
            "--output",
            str(output),
        ],
    )
    assert MODULE.main() == 0
    packet = json.loads(output.read_text())
    assert packet["repository_sha"] == "a" * 40
    assert packet["production_mutation_performed"] is False
