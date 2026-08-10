#!/usr/bin/env python3
"""Evaluate CROWN's governed operational-inclusive backend coverage metric."""

from __future__ import annotations

import argparse
import configparser
import json
import sys
from pathlib import Path
from typing import Any


class CoverageGovernanceError(ValueError):
    """Raised when the governed coverage boundary cannot be trusted."""


def _normalize(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise CoverageGovernanceError(f"Expected JSON object: {path}")
    return payload


def _numbers(summary: dict[str, Any], label: str) -> tuple[int, int, int]:
    try:
        statements = int(summary["num_statements"])
        covered = int(summary["covered_lines"])
        missing = int(summary["missing_lines"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CoverageGovernanceError(f"Incomplete coverage summary: {label}") from exc
    if min(statements, covered, missing) < 0 or covered + missing != statements:
        raise CoverageGovernanceError(f"Inconsistent coverage arithmetic: {label}")
    return statements, covered, missing


def _coveragerc_threshold(path: Path) -> float:
    parser = configparser.ConfigParser()
    if not parser.read(path, encoding="utf-8"):
        raise CoverageGovernanceError(f"Unable to read coverage configuration: {path}")
    try:
        return parser.getfloat("report", "fail_under")
    except (configparser.Error, ValueError) as exc:
        raise CoverageGovernanceError(".coveragerc must define [report] fail_under") from exc


def evaluate_coverage(
    coverage: dict[str, Any],
    boundary: dict[str, Any],
    *,
    repo_root: Path,
    coveragerc: Path,
) -> dict[str, Any]:
    threshold = float(boundary.get("threshold_percent", 0.0))
    configured_threshold = _coveragerc_threshold(coveragerc)
    if threshold != 75.0:
        raise CoverageGovernanceError("Governed coverage threshold must remain 75.0%")
    if configured_threshold != threshold:
        raise CoverageGovernanceError(
            f"Governed threshold and .coveragerc diverge: {threshold} vs {configured_threshold}"
        )

    exclusions = [_normalize(p) for p in boundary.get("excluded_nonruntime_paths", [])]
    operational = [_normalize(p) for p in boundary.get("operational_included_paths", [])]
    required_absent = [_normalize(p) for p in boundary.get("required_absent_paths", [])]
    for name, values in (
        ("excluded_nonruntime_paths", exclusions),
        ("operational_included_paths", operational),
        ("required_absent_paths", required_absent),
    ):
        if len(values) != len(set(values)):
            raise CoverageGovernanceError(f"Duplicate paths in {name}")

    overlap = sorted(set(exclusions) & set(operational))
    if overlap:
        raise CoverageGovernanceError(f"Operational source cannot be excluded: {overlap}")
    if set(required_absent) & (set(exclusions) | set(operational)):
        raise CoverageGovernanceError("Required-retired paths cannot have another classification")

    raw_files = coverage.get("files")
    raw_totals = coverage.get("totals")
    if not isinstance(raw_files, dict) or not isinstance(raw_totals, dict):
        raise CoverageGovernanceError("coverage.json must contain files and totals objects")
    files = {_normalize(str(path)): value for path, value in raw_files.items()}
    broad_statements, broad_covered, broad_missing = _numbers(raw_totals, "totals")

    removed_statements = removed_covered = removed_missing = 0
    applied_exclusions: list[dict[str, Any]] = []
    absent_exclusions: list[str] = []
    for path in exclusions:
        source_exists = (repo_root / path).exists()
        entry = files.get(path)
        if entry is None:
            if source_exists:
                raise CoverageGovernanceError(
                    f"Reviewed exclusion disappeared from broad coverage while source still exists: {path}"
                )
            absent_exclusions.append(path)
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get("summary"), dict):
            raise CoverageGovernanceError(f"Coverage entry has no summary: {path}")
        statements, covered, missing = _numbers(entry["summary"], path)
        removed_statements += statements
        removed_covered += covered
        removed_missing += missing
        applied_exclusions.append(
            {
                "path": path,
                "statements": statements,
                "covered_lines": covered,
                "missing_lines": missing,
            }
        )

    operational_checks: list[dict[str, Any]] = []
    for path in operational:
        exists = (repo_root / path).exists()
        measured = path in files
        if exists and not measured:
            raise CoverageGovernanceError(f"Governed operational paths disappeared from broad coverage: {path}")
        if not exists:
            raise CoverageGovernanceError(f"Governed operational path no longer exists: {path}")
        operational_checks.append({"path": path, "exists": exists, "measured": measured})

    retired_checks: list[dict[str, Any]] = []
    for path in required_absent:
        present = (repo_root / path).exists() or path in files
        retired_checks.append({"path": path, "absent": not present})
        if present:
            raise CoverageGovernanceError(f"Required-retired path is present: {path}")

    governed_statements = broad_statements - removed_statements
    governed_covered = broad_covered - removed_covered
    governed_missing = broad_missing - removed_missing
    if governed_statements <= 0 or governed_covered + governed_missing != governed_statements:
        raise CoverageGovernanceError("Governed coverage arithmetic is inconsistent")

    broad_percent = broad_covered * 100.0 / broad_statements if broad_statements else 0.0
    governed_percent = governed_covered * 100.0 / governed_statements
    threshold_pass = governed_percent >= threshold

    return {
        "schema_version": 1,
        "metric_name": boundary.get("metric_name"),
        "authority": boundary.get("authority", {}),
        "threshold_percent": threshold,
        "configured_fail_under_percent": configured_threshold,
        "threshold_pass": threshold_pass,
        "broad_repository_health": {
            "statements": broad_statements,
            "covered_lines": broad_covered,
            "missing_lines": broad_missing,
            "percent_covered_exact": broad_percent,
            "release_gate": False,
        },
        "governed_operational_inclusive": {
            "statements": governed_statements,
            "covered_lines": governed_covered,
            "missing_lines": governed_missing,
            "percent_covered_exact": governed_percent,
            "release_gate": True,
        },
        "boundary": {
            "applied_exclusions": applied_exclusions,
            "absent_exclusions": sorted(absent_exclusions),
            "operational_included_checks": operational_checks,
            "required_absent_checks": retired_checks,
            "new_unlisted_backend_files_counted_by_default": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage-json", required=True, type=Path)
    parser.add_argument("--boundary-config", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--coveragerc", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        result = evaluate_coverage(
            _load_json(args.coverage_json),
            _load_json(args.boundary_config),
            repo_root=args.repo_root.resolve(),
            coveragerc=args.coveragerc.resolve(),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (CoverageGovernanceError, OSError, json.JSONDecodeError) as exc:
        print(f"Governed coverage evaluation failed: {exc}", file=sys.stderr)
        return 2

    broad = result["broad_repository_health"]
    governed = result["governed_operational_inclusive"]
    print(f"Broad backend repository-health coverage: {broad['percent_covered_exact']:.6f}%")
    print(f"Governed operational-inclusive coverage: {governed['percent_covered_exact']:.6f}%")
    print(f"Governed threshold: {result['threshold_percent']:.1f}%")
    return 0 if result["threshold_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
