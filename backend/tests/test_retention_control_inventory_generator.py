import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_retention_control_inventory.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "retention_control_inventory", GENERATOR
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_is_deterministic_and_non_mutating():
    generator = load_generator()
    first = generator.build_inventory(REPO_ROOT)
    second = generator.build_inventory(REPO_ROOT)
    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_static_retention_control_inventory"
    assert first["legal_determination"] is False
    assert first["runtime_configuration_verified"] is False
    assert first["purge_execution_performed"] is False
    assert first["production_mutation_performed"] is False
    assert first["missing_sources"] == []
    assert first["failures"] == []
    source = GENERATOR.read_text(encoding="utf-8").lower()
    for token in (
        ".delete(",
        ".save(",
        ".update(",
        ".create(",
        "subprocess",
        "requests.",
        "os.system",
        "write_text(",
        "unlink(",
    ):
        assert token not in source


def test_inventory_conflicts_are_resolved_without_claiming_legal_approval():
    generator = load_generator()
    inventory = generator.build_inventory(REPO_ROOT)
    observations = inventory["observations"]

    assert observations["policy_pending_marker_present"] is False
    assert observations["soft_delete_policy_claim_present"] is False
    assert observations["direct_queryset_delete_present"] is False
    assert observations["legal_hold_field_present"] is True
    assert observations["purge_audit_model_present"] is True
    assert inventory["contradictions"] == []
    assert inventory["legal_determination"] is False
    assert inventory["runtime_configuration_verified"] is False


def test_inventory_evidences_required_safeguards():
    generator = load_generator()
    inventory = generator.build_inventory(REPO_ROOT)
    observations = inventory["observations"]

    assert observations["dry_run_control_present"] is True
    assert observations["approval_gate_present"] is True
    assert observations["tenant_scope_guard_present"] is True
    assert observations["batch_limit_present"] is True
    assert inventory["missing_safeguards"] == []
