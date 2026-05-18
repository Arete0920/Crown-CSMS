#!/usr/bin/env python3
"""
SOLOMON C1 Dry-Run Ingestion Executor

Purpose:
  Provide a safe dry-run-only ingestion execution boundary.

This script DOES NOT perform real ingestion unless every hard guard is passed.

Default behavior:
  - manifest-only
  - no indexing
  - no embeddings
  - no vector writes
  - no retrieval activation
  - no automation activation
  - no source mutation
  - no persistent corpus writes

Real ingestion remains blocked unless ALL are present:
  1. gate decision = ALLOW
  2. --execute-real-ingestion flag
  3. --confirm-token EXACTLY equals SOLOMON-C1-REAL-INGESTION
  4. isolated output target provided
  5. rollback manifest generated first
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.cwd()
GOV_DIR = ROOT / "governance" / "c1"

GATE_FILE = GOV_DIR / "gates" / "ingestion_activation_gate.json"
SIM_DIR = GOV_DIR / "simulation"
DRYRUN_DIR = GOV_DIR / "dry_run_ingestion"
ROLLBACK_DIR = GOV_DIR / "rollback"
RUNTIME_DIR = GOV_DIR / "runtime"
RUNTIME_DRYRUN_DIR = RUNTIME_DIR / "dry_run_ingestion"
RUNTIME_ROLLBACK_DIR = RUNTIME_DIR / "rollback"

INGESTION_MANIFEST = SIM_DIR / "ingestion_simulation_manifest.csv"
CHUNK_MANIFEST = SIM_DIR / "chunk_boundary_manifest.csv"
PROVENANCE_MANIFEST = SIM_DIR / "provenance_inheritance_manifest.csv"
QUARANTINE_MANIFEST = SIM_DIR / "quarantine_propagation_manifest.csv"

DRYRUN_REPORT = RUNTIME_DRYRUN_DIR / "DRY_RUN_INGESTION_REPORT.json"
DRYRUN_PLAN = RUNTIME_DRYRUN_DIR / "dry_run_ingestion_plan.csv"
ROLLBACK_MANIFEST = RUNTIME_ROLLBACK_DIR / "rollback_manifest.csv"

CONFIRM_TOKEN = "SOLOMON-C1-REAL-INGESTION"


def fail(message: str) -> None:
    print(f"FAILED: {message}")
    sys.exit(1)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"missing required file: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    """Write rows to a CSV file with normalized serialization."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(rows, key=lambda x: tuple(x.get(field, "") for field in fieldnames)):
            writer.writerow(row)


def write_json(path: Path, data: dict) -> None:
    """Write data to a JSON file with normalized serialization."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def assert_gate_allow() -> dict:
    gate = read_json(GATE_FILE)
    decision = gate.get("decision")
    if decision != "ALLOW":
        fail(f"ingestion gate is not ALLOW; current decision={decision}")
    return gate


def assert_manifest_contracts() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    ingestion_rows = read_csv_rows(INGESTION_MANIFEST)
    chunk_rows = read_csv_rows(CHUNK_MANIFEST)
    provenance_rows = read_csv_rows(PROVENANCE_MANIFEST)
    quarantine_rows = read_csv_rows(QUARANTINE_MANIFEST)

    if not ingestion_rows:
        fail("ingestion simulation manifest has zero rows")

    for row in ingestion_rows:
        if not row.get("source_id"):
            fail("ingestion manifest row missing source_id")
        if not row.get("custody_path"):
            fail(f"ingestion manifest row missing custody_path for {row.get('source_id')}")
        # Support both legacy and current simulation contracts.
        if not row.get("integrity_reference") and not row.get("sha256"):
            fail(
                f"ingestion manifest row missing integrity_reference/sha256 for {row.get('source_id')}"
            )

    for row in provenance_rows:
        if not row.get("source_id"):
            fail("provenance manifest row missing source_id")
        if not row.get("derived_artifact_id") and not row.get("simulated_artifact_id"):
            fail(
                f"provenance manifest row missing derived_artifact_id/simulated_artifact_id for {row.get('source_id')}"
            )

    return ingestion_rows, chunk_rows, provenance_rows, quarantine_rows


def generate_rollback_manifest(ingestion_rows: list[dict], output_target: Path | None) -> None:
    rows = []
    for row in ingestion_rows:
        source_id = row.get("source_id", "")
        rows.append(
            {
                "source_id": source_id,
                "rollback_action": "remove_derived_artifacts_for_source",
                "rollback_scope": "dry_run_only" if output_target is None else str(output_target),
                "status": "prepared_not_executed",
            }
        )

    write_csv(
        ROLLBACK_MANIFEST,
        rows,
        ["source_id", "rollback_action", "rollback_scope", "status"],
    )


def build_dryrun_plan(
    ingestion_rows: list[dict],
    chunk_rows: list[dict],
    provenance_rows: list[dict],
    quarantine_rows: list[dict],
) -> None:
    provenance_by_source = {}
    for row in provenance_rows:
        provenance_by_source.setdefault(row.get("source_id", ""), 0)
        provenance_by_source[row.get("source_id", "")] += 1

    chunk_by_source = {}
    for row in chunk_rows:
        chunk_by_source.setdefault(row.get("source_id", ""), 0)
        chunk_by_source[row.get("source_id", "")] += 1

    quarantine_sources = {row.get("source_id", "") for row in quarantine_rows}

    plan_rows = []
    for row in ingestion_rows:
        source_id = row.get("source_id", "")
        plan_rows.append(
            {
                "source_id": source_id,
                "custody_path": row.get("custody_path", ""),
                "integrity_reference": row.get("integrity_reference", row.get("sha256", "")),
                "planned_action": "would_ingest_manifest_only",
                "chunk_rows": chunk_by_source.get(source_id, 0),
                "provenance_rows": provenance_by_source.get(source_id, 0),
                "quarantine_applies": "YES" if source_id in quarantine_sources else "NO",
                "execution_status": "NOT_EXECUTED",
            }
        )

    write_csv(
        DRYRUN_PLAN,
        plan_rows,
        [
            "source_id",
            "custody_path",
            "integrity_reference",
            "planned_action",
            "chunk_rows",
            "provenance_rows",
            "quarantine_applies",
            "execution_status",
        ],
    )


def write_report(
    mode: str,
    gate: dict,
    ingestion_rows: list[dict],
    chunk_rows: list[dict],
    provenance_rows: list[dict],
    quarantine_rows: list[dict],
    real_ingestion_blocked: bool,
) -> None:
    RUNTIME_DRYRUN_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "mode": mode,
        "real_ingestion_blocked": real_ingestion_blocked,
        "gate_decision": gate.get("decision"),
        "counts": {
            "ingestion_rows": len(ingestion_rows),
            "chunk_rows": len(chunk_rows),
            "provenance_rows": len(provenance_rows),
            "quarantine_rows": len(quarantine_rows),
        },
        "boundary_controls": {
            "no_indexing": True,
            "no_embeddings": True,
            "no_vector_writes": True,
            "no_retrieval_activation": True,
            "no_automation_activation": True,
            "no_source_mutation": True,
        },
        "generated_files": [
            str(DRYRUN_PLAN.as_posix()),
            str(ROLLBACK_MANIFEST.as_posix()),
        ],
    }

    write_json(DRYRUN_REPORT, report)


def assert_real_ingestion_guards(args: argparse.Namespace) -> Path:
    if not args.execute_real_ingestion:
        fail("real ingestion blocked: missing --execute-real-ingestion")

    if args.confirm_token != CONFIRM_TOKEN:
        fail("real ingestion blocked: invalid or missing confirmation token")

    if not args.output_target:
        fail("real ingestion blocked: missing isolated --output-target")

    output_target = Path(args.output_target).resolve()

    if output_target.exists() and any(output_target.iterdir()):
        fail("real ingestion blocked: output target must be isolated and empty")

    output_target.mkdir(parents=True, exist_ok=True)
    return output_target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-real-ingestion", action="store_true")
    parser.add_argument("--confirm-token", default="")
    parser.add_argument("--output-target", default="")
    args = parser.parse_args()

    gate = assert_gate_allow()
    ingestion_rows, chunk_rows, provenance_rows, quarantine_rows = assert_manifest_contracts()

    build_dryrun_plan(ingestion_rows, chunk_rows, provenance_rows, quarantine_rows)
    generate_rollback_manifest(ingestion_rows, None)

    if not args.execute_real_ingestion:
        write_report(
            mode="DRY_RUN_ONLY",
            gate=gate,
            ingestion_rows=ingestion_rows,
            chunk_rows=chunk_rows,
            provenance_rows=provenance_rows,
            quarantine_rows=quarantine_rows,
            real_ingestion_blocked=True,
        )
        print("DRY_RUN_ONLY")
        print("Real ingestion blocked by default.")
        print(f"Dry-run plan: {DRYRUN_PLAN}")
        print(f"Rollback manifest: {ROLLBACK_MANIFEST}")
        print(f"Report: {DRYRUN_REPORT}")
        return

    output_target = assert_real_ingestion_guards(args)

    generate_rollback_manifest(ingestion_rows, output_target)

    fail(
        "real ingestion intentionally not implemented yet; "
        "guards passed but execution remains blocked until separate implementation gate"
    )


if __name__ == "__main__":
    main()
