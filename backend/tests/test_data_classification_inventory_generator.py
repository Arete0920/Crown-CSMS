import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_data_classification_inventory.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("data_classification_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_is_deterministic_sorted_and_fail_closed_on_known_anchors():
    generator = load_generator()
    first = generator.build_inventory(REPO_ROOT)
    second = generator.build_inventory(REPO_ROOT)

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_static_source_inventory"
    assert first["legal_determination"] is False
    assert first["missing_known_domain_anchors"] == []
    assert first["parse_failures"] == []
    assert first["record_count"] == len(first["records"])

    keys = [(item["path"], item["model"], item["field"]) for item in first["records"]]
    assert keys == sorted(keys)
    assert len(keys) == len(set(keys))


def test_inventory_contains_sensitive_identity_and_school_data_categories(tmp_path):
    generator = load_generator()
    inventory = generator.build_inventory(REPO_ROOT)
    categories = {record["sensitivity"] for record in inventory["records"]}

    assert "confidential_identity" in categories
    assert "confidential_academic" in categories
    assert inventory["record_count"] > 0

    output = tmp_path / "data-classification.json"
    output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["legal_determination"] is False


def test_inventory_parses_utf8_bom_prefixed_model_source(tmp_path):
    generator = load_generator()
    model_path = tmp_path / "backend" / "sample" / "models.py"
    model_path.parent.mkdir(parents=True)
    model_path.write_text(
        "from django.db import models\n\nclass StudentRecord(models.Model):\n    student_email = models.EmailField()\n",
        encoding="utf-8-sig",
    )

    inventory = generator.build_inventory(tmp_path)

    assert inventory["parse_failures"] == []
    assert inventory["records"] == [
        {
            "path": "backend/sample/models.py",
            "model": "StudentRecord",
            "field": "student_email",
            "field_type": "models.EmailField",
            "sensitivity": "confidential_identity",
            "review_flags": [],
        }
    ]


def test_generator_has_no_django_runtime_or_database_write_dependency():
    source = GENERATOR.read_text(encoding="utf-8").lower()

    assert "import django" not in source
    assert "from django" not in source
    assert ".objects" not in source
    assert "save(" not in source
    assert "delete(" not in source
    assert "transaction" not in source
    assert "automated_classification_review_required" in source
