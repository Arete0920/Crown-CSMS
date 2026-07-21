import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_manual_drill_execution_manifest.py"
FAILED_SHA = "1" * 40
GOOD_SHA = "2" * 40


def load_generator():
    spec = importlib.util.spec_from_file_location("manual_drill_execution_manifest", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_is_deterministic_nonproduction_and_complete():
    generator = load_generator()
    first = generator.build_manifest(FAILED_SHA, GOOD_SHA)
    second = generator.build_manifest(FAILED_SHA, GOOD_SHA)

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "manual_nonproduction_drill_execution_manifest"
    assert first["execution_performed"] is False
    assert first["production_mutation_performed"] is False
    assert first["failures"] == []
    assert first["execution_count"] == 4
    assert [item["name"] for item in first["executions"]] == [
        "recovery_decision_unhealthy_runtime",
        "secrets_routine_rotation",
        "secrets_failed_rotation_recovery",
        "secrets_break_glass",
    ]
    assert all(item["production_mutation_performed"] is False for item in first["executions"])
    assert all(item["environment"] != "production" for item in first["executions"])


def test_manifest_fails_closed_on_invalid_or_equal_shas():
    generator = load_generator()

    invalid = generator.build_manifest("bad", GOOD_SHA)
    assert invalid["failures"]

    equal = generator.build_manifest(GOOD_SHA, GOOD_SHA)
    assert equal["failures"] == ["failed candidate and last-known-good SHA must differ"]


def test_generator_cannot_dispatch_or_call_networks():
    source = GENERATOR.read_text(encoding="utf-8").lower()
    for token in (
        "requests.",
        "urllib",
        "subprocess",
        "os.system",
        "gh workflow run",
        "workflow_dispatch(",
    ):
        assert token not in source
