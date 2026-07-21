import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "tools" / "check_manual_drill_readiness.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("manual_drill_readiness", CHECKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manual_drill_workflows_are_static_ready_and_manual_only():
    checker = load_checker()
    report = checker.build_report()

    assert report["schema_version"] == 1
    assert report["execution_performed"] is False
    assert report["production_mutation_performed"] is False
    assert report["failures"] == []
    assert [record["name"] for record in report["records"]] == ["recovery", "secrets"]
    assert all(record["ready"] for record in report["records"])


def test_checker_cannot_dispatch_or_mutate_workflows():
    source = CHECKER.read_text(encoding="utf-8").lower()
    for token in ("requests.", "urllib", "subprocess", "os.system", "gh workflow run", "workflow_dispatch("):
        assert token not in source
