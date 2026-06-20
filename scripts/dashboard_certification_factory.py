#!/usr/bin/env python3
"""CROWN dashboard certification factory verifier.

This script is intentionally non-promotional: it reads the dashboard batch manifest
and certification state register, then reports what is missing before any dashboard
can be called CERTIFIED. It does not update the matrix and does not certify dashboards.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("docs/dashboard-completion/dashboard-batch-manifest.json")
DEFAULT_STATE = Path("audit-artifacts/dashboard-completion/state/dashboard-certification-state.json")
DEFAULT_OUTPUT = Path("audit-artifacts/dashboard-completion/factory/dashboard-certification-factory-report.json")


CERTIFIED_DECISIONS = {
    "certified",
    "review_candidate_with_workaround",
}

PASS_VALUES = {
    "pass",
    "done",
    "recorded",
    "pass_unit_tests_accepted",
    "pass_gap_documented_and_accepted_for_internal_scope",
    "solo_developer_approved_workaround",
}


@dataclass(frozen=True)
class DashboardResult:
    batch_id: str
    dashboard_key: str
    status: str
    certification_decision: str
    missing_requirements: list[str]

    @property
    def certified(self) -> bool:
        return not self.missing_requirements


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def required_packet_files(manifest: dict[str, Any]) -> list[str]:
    return list(manifest.get("completion_standard", {}).get("required_evidence_packet_files", []))


def dashboard_entries(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for batch in manifest.get("batches", []):
        batch_id = str(batch["id"])
        for dashboard_key in batch.get("dashboards", []):
            entries.append((batch_id, str(dashboard_key)))
    return entries


def evidence_packet_path(state_entry: dict[str, Any] | None, dashboard_key: str) -> Path:
    if state_entry and state_entry.get("evidence_packet"):
        return Path(str(state_entry["evidence_packet"]))
    return Path("audit-artifacts/dashboard-completion/evidence-packets") / f"{dashboard_key}.md"


def missing_packet_references(packet_path: Path, packet_files: list[str]) -> list[str]:
    if packet_path.is_dir():
        return [
            f"packet_reference:{required_file}"
            for required_file in packet_files
            if not (packet_path / required_file).exists()
        ]
    # Legacy packet format is a single markdown file; path existence is the
    # required gate for this format.
    return []


def _proof_value(proof: dict[str, Any], key: str, aliases: list[str] | None = None) -> str:
    candidates = [key] + (aliases or [])
    for candidate in candidates:
        if candidate in proof:
            return str(proof.get(candidate, "not_verified"))
    return "not_verified"


def _decision_indicates_certified(status: str, decision: str) -> bool:
    return decision in CERTIFIED_DECISIONS and status.startswith("certified")


def _is_pass_value(value: str, *, key: str) -> bool:
    if key == "matrix_promotion":
        return value in PASS_VALUES
    return value in PASS_VALUES


def inspect_dashboard(
    batch_id: str,
    dashboard_key: str,
    state_dashboards: dict[str, Any],
    packet_files: list[str],
) -> DashboardResult:
    state_entry = state_dashboards.get(dashboard_key)
    missing: list[str] = []

    if not state_entry:
        missing.append("state_register_entry")
        status = "missing_state_entry"
        decision = "not_certified"
    else:
        status = str(state_entry.get("state", "unknown"))
        decision = str(state_entry.get("certification_decision", "not_certified"))

    packet_path = evidence_packet_path(state_entry, dashboard_key)
    if not packet_path.exists():
        missing.append("evidence_packet_path")
    else:
        missing.extend(missing_packet_references(packet_path, packet_files))

    proof = state_entry.get("proof", {}) if state_entry else {}
    required_proof = [
        ("api_permission", []),
        ("tenant_isolation", ["tenant_behavior"]),
        ("browser_rendered_title_metrics", []),
        ("independent_review", ["solo_developer_workaround"]),
        ("matrix_promotion", []),
    ]
    for key, aliases in required_proof:
        value = _proof_value(proof, key, aliases)
        if not _is_pass_value(value, key=key):
            missing.append(f"proof:{key}:{value}")

    if not _decision_indicates_certified(status, decision):
        missing.append(f"certification_decision:{decision}")

    return DashboardResult(
        batch_id=batch_id,
        dashboard_key=dashboard_key,
        status=status,
        certification_decision=decision,
        missing_requirements=sorted(set(missing)),
    )


def build_report(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    packet_files = required_packet_files(manifest)
    state_dashboards = state.get("dashboards", {})
    results = [
        inspect_dashboard(batch_id, dashboard_key, state_dashboards, packet_files)
        for batch_id, dashboard_key in dashboard_entries(manifest)
    ]

    certified_count = sum(1 for result in results if result.certified)
    total = len(results)

    batch_summary: dict[str, dict[str, int]] = {}
    for result in results:
        summary = batch_summary.setdefault(result.batch_id, {"total": 0, "certified": 0, "blocked": 0})
        summary["total"] += 1
        if result.certified:
            summary["certified"] += 1
        else:
            summary["blocked"] += 1

    return {
        "schema_version": "2026-06-19.dashboard-certification-factory-report.v1",
        "status": "verification_report_not_certification",
        "totals": {
            "dashboards_total": total,
            "certified": certified_count,
            "blocked": total - certified_count,
            "certification_rate_percent": round((certified_count / total) * 100, 2) if total else 0,
        },
        "batch_summary": batch_summary,
        "dashboards": [
            {
                "batch_id": result.batch_id,
                "dashboard_key": result.dashboard_key,
                "state": result.status,
                "certification_decision": result.certification_decision,
                "certified": result.certified,
                "missing_requirements": result.missing_requirements,
            }
            for result in results
        ],
        "non_claims": [
            "This report does not certify any dashboard.",
            "This report does not approve sandbox, pilot, production, or release GO.",
            "Only independently reviewed matrix promotion to CERTIFIED completes a dashboard.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dashboard certification factory state.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    state = load_json(args.state)
    report = build_report(manifest, state)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"DASHBOARD_CERTIFICATION_FACTORY_REPORT={args.output}")
    print(f"DASHBOARDS_TOTAL={report['totals']['dashboards_total']}")
    print(f"CERTIFIED={report['totals']['certified']}")
    print(f"BLOCKED={report['totals']['blocked']}")
    print(f"STATUS={report['status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
