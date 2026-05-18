#!/usr/bin/env python3
"""Validate SOLOMON C1 governance control-plane artifacts.

This validator enforces governance-only guardrails and fails closed.
It does not ingest, index, enrich, or activate any downstream workflow.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "c1"

REQUIRED_FILES = [
    GOV / "00_BOUNDARY.md",
    GOV / "01_CANONICAL_SOURCE_ACCEPTANCE_CRITERIA.md",
    GOV / "02_PROVENANCE_TAXONOMY.md",
    GOV / "03_CHAIN_OF_CUSTODY_STANDARD.md",
    GOV / "04_EVIDENCE_ADMISSIBILITY_RULES.md",
    GOV / "05_REVIEW_CHECKLIST.md",
    GOV / "06_APPROVAL_MATRIX.md",
    GOV / "07_QUARANTINE_AND_REVOCATION.md",
    GOV / "schemas" / "source_candidate.schema.json",
    GOV / "schemas" / "evidence_record.schema.json",
    GOV / "schemas" / "review_decision.schema.json",
    GOV / "registers" / "source_candidates.csv",
    GOV / "registers" / "evidence_register.csv",
    GOV / "registers" / "decision_register.csv",
    GOV / "registers" / "review_queue.csv",
    GOV / "registers" / "human_approval_queue.csv",
    GOV / "registers" / "risk_exceptions.csv",
    GOV / "review_packets" / "C1_REVIEW_PACKET.md",
    GOV / "reports" / "C1_READINESS_STATUS.md",
    GOV / "simulation" / "ingestion_simulation_manifest.csv",
    GOV / "simulation" / "chunk_boundary_manifest.csv",
    GOV / "simulation" / "provenance_inheritance_manifest.csv",
    GOV / "simulation" / "quarantine_propagation_manifest.csv",
    GOV / "simulation" / "INGESTION_SIMULATION_REPORT.md",
]

EXPECTED_HEADERS = {
    "source_candidates.csv": [
        "source_id",
        "title",
        "source_type",
        "origin_owner",
        "acquisition_method",
        "acquired_by",
        "acquired_at",
        "custody_path",
        "version_or_date",
        "integrity_reference",
        "rights_basis",
        "provenance_tier",
        "review_status",
        "reviewer",
        "decision_date",
        "decision_rationale",
        "risk_flags",
    ],
    "evidence_register.csv": [
        "evidence_id",
        "source_id",
        "evidence_type",
        "description",
        "origin",
        "recorded_by",
        "recorded_at",
        "evidence_location",
    ],
    "decision_register.csv": [
        "decision_id",
        "source_id",
        "decision",
        "reviewer",
        "decision_date",
        "rationale",
        "conditions",
    ],
    "review_queue.csv": [
        "source_id",
        "title",
        "custody_path",
        "sha256",
        "file_size_bytes",
        "source_type",
        "provisional_tier",
        "risk_score",
        "risk_flags",
        "recommended_decision",
        "evidence_gap",
        "human_action_required",
    ],
    "human_approval_queue.csv": [
        "source_id",
        "title",
        "custody_path",
        "sha256",
        "file_size_bytes",
        "source_type",
        "provisional_tier",
        "risk_score",
        "risk_flags",
        "recommended_decision",
        "evidence_gap",
        "human_action_required",
    ],
    "risk_exceptions.csv": [
        "source_id",
        "title",
        "custody_path",
        "risk_score",
        "risk_flags",
        "required_action",
    ],
    "ingestion_simulation_manifest.csv": [
        "source_id",
        "title",
        "custody_path",
        "sha256",
        "file_size_bytes",
        "source_type",
        "provenance_tier",
        "rights_basis",
        "simulated_ingest_status",
        "simulated_chunk_count",
        "source_version_or_date",
    ],
    "chunk_boundary_manifest.csv": [
        "source_id",
        "chunk_id",
        "byte_start",
        "byte_end",
        "chunk_size_bytes",
        "overlap_bytes",
        "chunking_policy",
        "source_sha256",
    ],
    "provenance_inheritance_manifest.csv": [
        "source_id",
        "source_sha256",
        "simulated_artifact_id",
        "inherited_provenance_tier",
        "inherited_rights_basis",
        "inheritance_mode",
    ],
    "quarantine_propagation_manifest.csv": [
        "source_id",
        "decision",
        "quarantine_reason",
        "propagation_action",
    ],
}

ALLOWED_DECISIONS = {
    "APPROVED_CANONICAL",
    "APPROVED_REFERENCE_ONLY",
    "QUARANTINED_PENDING_REVIEW",
    "REJECTED",
    "ESCALATED",
}


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def check_required_files() -> None:
    missing = [str(p) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        _fail("missing required files:\n- " + "\n- ".join(missing))
    _ok(f"all required files present ({len(REQUIRED_FILES)})")


def check_json_schemas() -> None:
    for name in [
        "source_candidate.schema.json",
        "evidence_record.schema.json",
        "review_decision.schema.json",
    ]:
        path = GOV / "schemas" / name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _fail(f"invalid JSON in {path}: {exc}")

        for key in ("$schema", "title", "type", "properties"):
            if key not in data:
                _fail(f"schema {name} missing key: {key}")
    _ok("schema JSON parse and required keys")


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            return []


def check_csv_headers() -> None:
    reg = GOV / "registers"
    for file_name, expected in EXPECTED_HEADERS.items():
        if file_name in {
            "ingestion_simulation_manifest.csv",
            "chunk_boundary_manifest.csv",
            "provenance_inheritance_manifest.csv",
            "quarantine_propagation_manifest.csv",
        }:
            path = GOV / "simulation" / file_name
        else:
            path = reg / file_name
        actual = _read_header(path)
        if actual != expected:
            _fail(
                f"header mismatch for {file_name}\nexpected: {expected}\nactual:   {actual}"
            )
    _ok("register CSV headers match expected contract")


def check_normalized_paths() -> None:
    """Ensure deterministic artifacts do not carry machine-specific absolute paths."""
    for file_name in [
        "source_candidates.csv",
        "review_queue.csv",
        "human_approval_queue.csv",
        "risk_exceptions.csv",
        "ingestion_simulation_manifest.csv",
    ]:
        if file_name == "ingestion_simulation_manifest.csv":
            path = GOV / "simulation" / file_name
        else:
            path = GOV / "registers" / file_name

        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if "custody_path" not in (reader.fieldnames or []):
                continue
            for i, row in enumerate(reader, start=2):
                custody = (row.get("custody_path") or "").strip()
                if not custody:
                    continue
                if ":\\" in custody or "\\" in custody:
                    _fail(f"non-normalized custody_path at {path}:{i}: {custody}")

    _ok("custody_path values are normalized and non-machine-specific")


def check_boundary_docs() -> None:
    boundary = (GOV / "00_BOUNDARY.md").read_text(encoding="utf-8")
    for phrase in [
        "No ingestion",
        "No indexing",
        "No semantic enrichment",
        "No automation activation",
    ]:
        if phrase not in boundary:
            _fail(f"boundary doc missing phrase: {phrase}")

    readiness = (GOV / "reports" / "C1_READINESS_STATUS.md").read_text(encoding="utf-8")
    if "NO-GO for ingestion." not in readiness:
        _fail("readiness report must state NO-GO for ingestion")

    packet = (GOV / "review_packets" / "C1_REVIEW_PACKET.md").read_text(encoding="utf-8")
    if "No file becomes canonical unless the sole human approver records an explicit decision" not in packet:
        _fail("review packet missing human approval rule")

    _ok("boundary/readiness/review packet guardrails present")


def check_decision_register_values() -> None:
    path = GOV / "registers" / "decision_register.csv"
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            decision = (row.get("decision") or "").strip()
            if decision and decision not in ALLOWED_DECISIONS:
                _fail(f"invalid decision value at {path}:{i}: {decision}")
    _ok("decision register decision values valid")


def check_queue_consistency() -> None:
    review_path = GOV / "registers" / "review_queue.csv"
    approval_path = GOV / "registers" / "human_approval_queue.csv"
    risk_path = GOV / "registers" / "risk_exceptions.csv"

    with review_path.open("r", encoding="utf-8", newline="") as f:
        review_rows = list(csv.DictReader(f))
    with approval_path.open("r", encoding="utf-8", newline="") as f:
        approval_rows = list(csv.DictReader(f))
    with risk_path.open("r", encoding="utf-8", newline="") as f:
        risk_rows = list(csv.DictReader(f))

    review_ids = {r.get("source_id", "") for r in review_rows}
    approval_ids = {r.get("source_id", "") for r in approval_rows}
    risk_ids = {r.get("source_id", "") for r in risk_rows}

    if not approval_ids.issubset(review_ids):
        _fail("human_approval_queue contains source_ids missing from review_queue")
    if not risk_ids.issubset(review_ids):
        _fail("risk_exceptions contains source_ids missing from review_queue")

    allowed_for_approval = {"READY_FOR_HUMAN_APPROVAL", "NEEDS_REVIEW"}
    for row in approval_rows:
        if row.get("recommended_decision") not in allowed_for_approval:
            _fail("human_approval_queue has disallowed recommended_decision")

    _ok("queue consistency checks passed")


def main() -> None:
    print(f"Validating C1 control plane at: {GOV}")
    check_required_files()
    check_json_schemas()
    check_csv_headers()
    check_normalized_paths()
    check_boundary_docs()
    check_decision_register_values()
    check_queue_consistency()
    print("SUCCESS: C1 governance control plane validation passed.")


if __name__ == "__main__":
    main()
