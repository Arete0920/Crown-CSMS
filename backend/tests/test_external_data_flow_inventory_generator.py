import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_external_data_flow_inventory.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("external_data_flow_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_is_deterministic_source_backed_and_non_authoritative():
    generator = load_generator()
    first = generator.build_inventory(REPO_ROOT)
    second = generator.build_inventory(REPO_ROOT)

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_static_external_data_flow_inventory"
    assert first["legal_determination"] is False
    assert first["production_configuration_verified"] is False
    assert first["missing_sources"] == []
    assert first["failures"] == []
    assert first["record_count"] == len(first["records"])
    assert [record["name"] for record in first["records"]] == sorted(record["name"] for record in first["records"])
    assert all(record["evidence_sources"] for record in first["records"])
    assert all(record["contract_or_dpa_status"] == "not_verified" for record in first["records"])
    assert all(record["processing_location"] == "not_verified" for record in first["records"])


def test_inventory_captures_expected_flows_and_flags_deferred_stripe_reference():
    generator = load_generator()
    inventory = generator.build_inventory(REPO_ROOT)
    observed = {record["name"] for record in inventory["records"]}

    assert {"Microsoft Graph", "Azure App Service", "PostgreSQL", "Redis/Celery", "Azure Key Vault"} <= observed
    deferred = {record["name"]: record for record in inventory["stale_or_deferred_references"]}
    assert deferred["Stripe"]["production_active"] is False
    assert "not selected or authorized" in deferred["Stripe"]["reason"]


def test_generator_is_read_only_and_contains_no_network_or_repository_mutation():
    source = GENERATOR.read_text(encoding="utf-8").lower()
    for token in (
        "requests.",
        "urllib",
        "subprocess",
        "os.system",
        "write_text(",
        "unlink(",
        "update_file",
        "delete_file",
    ):
        assert token not in source
