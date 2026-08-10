import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_PATH = REPO_ROOT / "scripts" / "release" / "evaluate_backend_coverage.py"
BOUNDARY_PATH = REPO_ROOT / "scripts" / "release" / "backend_coverage_boundary.json"
LOCKED_EVIDENCE_PATH = (
    REPO_ROOT / "docs" / "release" / "evidence" / "request-serving-coverage-b191be5.json"
)
SPEC = importlib.util.spec_from_file_location("evaluate_backend_coverage", EVALUATOR_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def _entry(statements, covered):
    return {
        "summary": {
            "num_statements": statements,
            "covered_lines": covered,
            "missing_lines": statements - covered,
            "excluded_lines": 0,
        }
    }


def _coverage(files):
    statements = sum(v["summary"]["num_statements"] for v in files.values())
    covered = sum(v["summary"]["covered_lines"] for v in files.values())
    return {
        "files": files,
        "totals": {
            "num_statements": statements,
            "covered_lines": covered,
            "missing_lines": statements - covered,
            "excluded_lines": 0,
        },
    }


def _coveragerc(tmp_path, threshold=75):
    path = tmp_path / ".coveragerc"
    path.write_text(f"[report]\nfail_under = {threshold}\n", encoding="utf-8")
    return path


def _config(**overrides):
    config = {
        "metric_name": "operational-inclusive backend application coverage",
        "threshold_percent": 75.0,
        "authority": {"evidence_pr": 1860, "verification_pr": 1862},
        "excluded_nonruntime_paths": ["backend/demo_seed.py"],
        "operational_included_paths": ["backend/send_outbox.py"],
        "required_absent_paths": ["backend/fix_schema_drift.py"],
    }
    config.update(overrides)
    return config


def _evaluate(coverage, config, tmp_path, threshold=75):
    return MODULE.evaluate_coverage(
        coverage,
        config,
        repo_root=tmp_path,
        coveragerc=_coveragerc(tmp_path, threshold),
    )


def test_broad_health_can_fail_while_governed_release_gate_passes(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "send_outbox.py").write_text("# ops\n", encoding="utf-8")
    result = _evaluate(
        _coverage(
            {
                "backend/runtime.py": _entry(75, 60),
                "backend/send_outbox.py": _entry(25, 15),
                "backend/demo_seed.py": _entry(100, 0),
            }
        ),
        _config(),
        tmp_path,
    )

    assert result["broad_repository_health"]["percent_covered_exact"] == pytest.approx(37.5)
    assert result["governed_operational_inclusive"]["percent_covered_exact"] == pytest.approx(75.0)
    assert result["threshold_pass"] is True


def test_new_unlisted_backend_file_is_counted_by_default(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "send_outbox.py").write_text("# ops\n", encoding="utf-8")
    result = _evaluate(
        _coverage(
            {
                "backend/runtime.py": _entry(80, 80),
                "backend/send_outbox.py": _entry(20, 20),
                "backend/new_runtime.py": _entry(100, 0),
                "backend/demo_seed.py": _entry(100, 0),
            }
        ),
        _config(),
        tmp_path,
    )

    assert result["governed_operational_inclusive"]["statements"] == 200
    assert result["governed_operational_inclusive"]["covered_lines"] == 100
    assert result["threshold_pass"] is False
    assert result["boundary"]["new_unlisted_backend_files_counted_by_default"] is True


def test_operational_source_cannot_be_excluded(tmp_path):
    with pytest.raises(MODULE.CoverageGovernanceError, match="cannot be excluded"):
        _evaluate(
            _coverage({"backend/send_outbox.py": _entry(10, 10)}),
            _config(excluded_nonruntime_paths=["backend/send_outbox.py"]),
            tmp_path,
        )


def test_threshold_must_remain_75_and_match_coveragerc(tmp_path):
    with pytest.raises(MODULE.CoverageGovernanceError, match="diverge"):
        _evaluate(
            _coverage({"backend/runtime.py": _entry(10, 10)}),
            _config(excluded_nonruntime_paths=["backend/demo_seed.py"], operational_included_paths=[]),
            tmp_path,
            threshold=74,
        )


def test_retired_destructive_path_reappearance_fails_closed(tmp_path):
    retired = tmp_path / "backend" / "fix_schema_drift.py"
    retired.parent.mkdir(parents=True)
    retired.write_text("# forbidden\n", encoding="utf-8")
    with pytest.raises(MODULE.CoverageGovernanceError, match="Required-retired"):
        _evaluate(
            _coverage({"backend/runtime.py": _entry(10, 10)}),
            _config(excluded_nonruntime_paths=["backend/demo_seed.py"], operational_included_paths=[]),
            tmp_path,
        )


def test_current_boundary_exactly_partitions_locked_pr1860_paths():
    boundary = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    locked = json.loads(LOCKED_EVIDENCE_PATH.read_text(encoding="utf-8"))
    locked_paths = set(locked["boundary_exclusions"]["paths"])
    classified = (
        set(boundary["excluded_nonruntime_paths"])
        | set(boundary["operational_included_paths"])
        | set(boundary["required_absent_paths"])
    )

    assert len(locked_paths) == 64
    assert len(boundary["excluded_nonruntime_paths"]) == 58
    assert len(boundary["operational_included_paths"]) == 5
    assert len(boundary["required_absent_paths"]) == 1
    assert classified == locked_paths
    assert boundary["threshold_percent"] == 75.0
