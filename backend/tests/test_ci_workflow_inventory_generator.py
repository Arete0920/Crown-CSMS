import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_ci_workflow_inventory.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("ci_workflow_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_is_deterministic_sorted_and_non_destructive():
    generator = load_generator()
    first = generator.build_inventory()
    second = generator.build_inventory()

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_static_workflow_inventory"
    assert first["workflow_count"] == len(first["records"])
    paths = [record["path"] for record in first["records"]]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))

    source = GENERATOR.read_text(encoding="utf-8").lower()
    for token in ("unlink(", "rmtree", "write_text(", "update_file", "delete_file"):
        assert token not in source


def test_inventory_captures_core_workflows_and_job_metadata():
    generator = load_generator()
    inventory = generator.build_inventory()
    observed = {record["path"]: record for record in inventory["records"]}

    assert ".github/workflows/ci.yml" in observed
    assert ".github/workflows/tests.yml" in observed
    assert ".github/workflows/codeql.yml" in observed
    assert all(record["job_count"] == len(record["jobs"]) for record in inventory["records"])


def test_job_extraction_ignores_event_keys_under_on_mapping():
    generator = load_generator()
    workflow = """name: sample
on:
  pull_request:
  workflow_dispatch:
jobs:
  verify:
    runs-on: ubuntu-latest
    steps: []
"""

    assert generator.extract_jobs(workflow) == ["verify"]
