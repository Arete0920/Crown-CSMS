import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_identity_consumer_inventory.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("identity_consumer_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_is_deterministic_sorted_and_complete():
    generator = load_generator()
    first = generator.build_inventory(REPO_ROOT)
    second = generator.build_inventory(REPO_ROOT)

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_static_inventory"
    assert first["missing_known_anchors"] == {}
    assert first["record_count"] == len(first["records"])

    paths = [record["path"] for record in first["records"]]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))

    observed = {record["path"]: record for record in first["records"]}
    assert "canonical_core" in observed["backend/core/models.py"]["families"]
    assert "canonical_core" in observed[
        "backend/guardian_household_wizard/containment_views.py"
    ]["families"]
    assert "canonical_core" in observed["backend/crown_api/views_students.py"]["families"]
    assert "households_compatibility" in observed[
        "backend/households/models.py"
    ]["families"]
    assert "households_compatibility" in observed[
        "backend/applications/views_admissions.py"
    ]["families"]
    assert "crown_api_compatibility" in observed[
        "backend/crown_api/models_households.py"
    ]["families"]


def test_inventory_output_is_machine_readable_and_read_only(tmp_path):
    generator = load_generator()
    inventory = generator.build_inventory(REPO_ROOT)
    output = tmp_path / "identity-consumers.json"
    output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["record_count"] > 0
    assert payload["missing_known_anchors"] == {}

    source = GENERATOR.read_text(encoding="utf-8").lower()
    assert "import django" not in source
    assert "from django" not in source
    assert "save(" not in source
    assert "delete(" not in source
    assert "transaction.atomic" not in source
    assert "connection.cursor" not in source
