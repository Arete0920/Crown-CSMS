import json
from pathlib import Path


def test_schema_budget_exists():
    path = Path("docs/release/SCHEMA_W002_BUDGET.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "current_max" in data
    assert "next_target" in data
    assert "goal" in data


def test_schema_scripts_exist():
    required = [
        "scripts/release/schema_w002_inventory.py",
        "scripts/release/patch_schema_function_views.py",
        "scripts/release/patch_schema_apiview_methods.py",
        "scripts/release/schema_gate.py",
        "scripts/release/route_catalog_release.py",
        "scripts/release/update_schema_progress_doc.py",
    ]
    for item in required:
        assert Path(item).exists(), item


def test_schema_summary_if_present_is_valid():
    path = Path("audit-artifacts/release-verify/schema_w002_summary.json")
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "total_w002" in data
    assert "budget_current_max" in data
    assert "budget_pass" in data