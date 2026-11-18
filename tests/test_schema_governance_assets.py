import json
from pathlib import Path


def test_schema_budget_exists():
    path = Path("docs/release/SCHEMA_W002_BUDGET.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["metric"] == "unique_schema_generation_errors"
    assert "current_max" in data
    assert "next_target" in data
    assert data["goal"] == 0


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
    assert data["metric"] == "unique_schema_generation_errors"
    assert "total_w002" in data  # compatibility alias for older artifact consumers
    assert "unique_schema_errors" in data
    assert "total_schema_errors" in data
    assert "unique_schema_warnings" in data
    assert "schema_export_returncode" in data
    assert "budget_current_max" in data
    assert "budget_pass" in data
    assert "production_ready" in data

def test_schema_governance_uses_repository_dependencies_and_real_export():
    workflow = Path(".github/workflows/schema-governance.yml").read_text(encoding="utf-8")
    inventory = Path("scripts/release/schema_w002_inventory.py").read_text(encoding="utf-8")
    assert "drf-spectacular==0.27.2" not in workflow
    assert "python -m pip check" in workflow
    assert "OpenAPI schema error inventory" in workflow
    assert '"spectacular"' in inventory
    assert '"check"' not in inventory
    assert '"--deploy"' not in inventory


def test_schema_patch_inventory_paths_are_confined(tmp_path):
    import importlib.util
    import pytest

    backend = tmp_path / "backend" / "classes"
    backend.mkdir(parents=True)
    valid = backend / "views.py"
    valid.write_text("pass\n", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("pass\n", encoding="utf-8")
    non_python = backend / "notes.txt"
    non_python.write_text("ignore\n", encoding="utf-8")
    symlink = backend / "linked.py"
    try:
        symlink.symlink_to(outside)
    except (OSError, NotImplementedError):
        symlink = None

    for file_name in (
        "patch_schema_apiview_methods.py",
        "patch_schema_function_views.py",
    ):
        source_path = Path("scripts/release") / file_name
        spec = importlib.util.spec_from_file_location(
            "schema_path_test_" + source_path.stem, source_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT = tmp_path

        assert module._inventory_target({"file": "backend/classes/views.py"}) == valid
        assert module._inventory_target({"file": "unknown"}) is None
        assert module._inventory_target({"file": "backend/classes/missing.py"}) is None
        for candidate in (
            "../outside.py",
            "backend/../../outside.py",
            "backend/classes/../../../outside.py",
            str(outside),
            "backend\\\\classes\\\\views.py",
            "backend/classes/notes.txt",
            "scripts/release/patch_schema_apiview_methods.py",
        ):
            with pytest.raises(ValueError, match="backend Python file"):
                module._inventory_target({"file": candidate})
        if symlink is not None:
            with pytest.raises(ValueError, match="regular in-repository file"):
                module._inventory_target({"file": "backend/classes/linked.py"})
        with pytest.raises(ValueError, match="invalid schema inventory"):
            module._inventory_target({"no_file": "backend/classes/views.py"})

        inventory = tmp_path / "inventory.json"
        module.INVENTORY = inventory
        inventory.write_text(json.dumps([
            {"file": "unknown"},
            {"file": "backend/classes/views.py"},
            {"file": "../outside.py"},
        ]), encoding="utf-8")
        with pytest.raises(ValueError, match="backend Python file"):
            module.target_files()
        assert outside.read_text(encoding="utf-8") == "pass\n"
