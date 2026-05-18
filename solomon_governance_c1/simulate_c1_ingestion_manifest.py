#!/usr/bin/env python3
"""SOLOMON C1 deterministic ingestion simulator (manifest-only).

This tool simulates what WOULD be ingested after human approval without performing ingestion.

Hard guarantees:
- No corpus ingestion
- No indexing
- No embedding/vector writes
- No retrieval activation
- No automation activation
- No mutation outside governance/c1/simulation outputs
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "c1_candidate_sources"
GOV_DIR = ROOT / "governance" / "c1"
REG_DIR = GOV_DIR / "registers"
SIM_DIR = GOV_DIR / "simulation"

DECISION_REGISTER = REG_DIR / "decision_register.csv"
SOURCE_CANDIDATES = REG_DIR / "source_candidates.csv"
HUMAN_APPROVAL_QUEUE = REG_DIR / "human_approval_queue.csv"
RISK_EXCEPTIONS = REG_DIR / "risk_exceptions.csv"

INGESTION_MANIFEST = SIM_DIR / "ingestion_simulation_manifest.csv"
CHUNK_MANIFEST = SIM_DIR / "chunk_boundary_manifest.csv"
PROVENANCE_MANIFEST = SIM_DIR / "provenance_inheritance_manifest.csv"
QUARANTINE_MANIFEST = SIM_DIR / "quarantine_propagation_manifest.csv"
SIM_REPORT = SIM_DIR / "INGESTION_SIMULATION_REPORT.md"

# Deterministic chunking policy (simulation only)
DEFAULT_CHUNK_BYTES = 4096
DEFAULT_OVERLAP_BYTES = 256


@dataclass
class IngestionRow:
    source_id: str
    title: str
    custody_path: str
    sha256: str
    file_size_bytes: int
    source_type: str
    provenance_tier: str
    rights_basis: str
    simulated_ingest_status: str
    simulated_chunk_count: int
    source_version_or_date: str


@dataclass
class ChunkRow:
    source_id: str
    chunk_id: str
    byte_start: int
    byte_end: int
    chunk_size_bytes: int
    overlap_bytes: int
    chunking_policy: str
    source_sha256: str


@dataclass
class ProvenanceRow:
    source_id: str
    source_sha256: str
    simulated_artifact_id: str
    inherited_provenance_tier: str
    inherited_rights_basis: str
    inheritance_mode: str


@dataclass
class QuarantineRow:
    source_id: str
    decision: str
    quarantine_reason: str
    propagation_action: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _safe_chunk_count(size_bytes: int, chunk_bytes: int, overlap_bytes: int) -> int:
    if size_bytes <= 0:
        return 0
    if chunk_bytes <= overlap_bytes:
        return 1
    step = chunk_bytes - overlap_bytes
    return 1 + max(0, (size_bytes - chunk_bytes + step - 1) // step)


def build_chunks(source_id: str, file_size: int, source_sha: str) -> list[ChunkRow]:
    rows: list[ChunkRow] = []
    if file_size <= 0:
        return rows

    chunk_bytes = DEFAULT_CHUNK_BYTES
    overlap = DEFAULT_OVERLAP_BYTES
    step = max(1, chunk_bytes - overlap)

    start = 0
    idx = 1
    while start < file_size:
        end = min(file_size, start + chunk_bytes)
        rows.append(
            ChunkRow(
                source_id=source_id,
                chunk_id=f"{source_id}-CHUNK-{idx:04d}",
                byte_start=start,
                byte_end=end,
                chunk_size_bytes=end - start,
                overlap_bytes=overlap if idx > 1 else 0,
                chunking_policy=f"fixed_bytes:{chunk_bytes},overlap:{overlap}",
                source_sha256=source_sha,
            )
        )
        if end >= file_size:
            break
        start += step
        idx += 1

    return rows


def _sim_artifact_id(source_id: str, source_sha: str) -> str:
    short = hashlib.sha256(f"{source_id}:{source_sha}".encode("utf-8")).hexdigest()[:12]
    return f"SIM-{source_id}-{short}"


def build_report(
    approved: int,
    quarantined: int,
    rejected: int,
    simulated_chunks: int,
) -> str:
    return f"""# C1 Ingestion Simulation Report

Generated: deterministic-artifact (runtime metadata intentionally excluded)

## Simulation Boundary

This is a deterministic simulation only.

- No ingestion performed
- No indexing performed
- No embedding/vector writes performed
- No retrieval activation performed
- No automation activation performed

## Decision Summary

| Decision | Count |
|---|---:|
| APPROVED_CANONICAL (simulated) | {approved} |
| QUARANTINED_PENDING_REVIEW | {quarantined} |
| REJECTED | {rejected} |

## Simulation Output Summary

| Output | Count |
|---|---:|
| Simulated ingestion manifest rows | {approved} |
| Simulated chunk rows | {simulated_chunks} |

## Readiness

NO-GO for real ingestion remains in effect.

Reason: This simulator produces manifests only and does not execute ingestion.
"""


def main() -> None:
    SIM_DIR.mkdir(parents=True, exist_ok=True)

    decisions = read_csv(DECISION_REGISTER)
    candidates = {r.get("source_id", ""): r for r in read_csv(SOURCE_CANDIDATES)}
    approval_queue = {r.get("source_id", ""): r for r in read_csv(HUMAN_APPROVAL_QUEUE)}

    approved_rows: list[IngestionRow] = []
    chunk_rows: list[ChunkRow] = []
    prov_rows: list[ProvenanceRow] = []
    quarantine_rows: list[QuarantineRow] = []

    approved_count = 0
    quarantined_count = 0
    rejected_count = 0

    for decision in decisions:
        source_id = (decision.get("source_id") or "").strip()
        outcome = (decision.get("decision") or "").strip()
        rationale = (decision.get("rationale") or "").strip()

        if not source_id or not outcome:
            continue

        c = candidates.get(source_id) or approval_queue.get(source_id)
        custody_path = (c or {}).get("custody_path", "")

        if outcome == "APPROVED_CANONICAL":
            approved_count += 1
            path = ROOT / custody_path if custody_path else None
            size = 0
            sha = ""
            if path and path.exists() and path.is_file():
                size = path.stat().st_size
                sha = (c or {}).get("integrity_reference", "")
                if sha.startswith("sha256:"):
                    sha = sha.split(":", 1)[1]
                if not sha:
                    # Fallback if source_candidates was not refreshed
                    h = hashlib.sha256()
                    with path.open("rb") as f:
                        for block in iter(lambda: f.read(1024 * 1024), b""):
                            h.update(block)
                    sha = h.hexdigest()

            chunk_count = _safe_chunk_count(size, DEFAULT_CHUNK_BYTES, DEFAULT_OVERLAP_BYTES)
            approved_rows.append(
                IngestionRow(
                    source_id=source_id,
                    title=(c or {}).get("title", ""),
                    custody_path=custody_path,
                    sha256=sha,
                    file_size_bytes=size,
                    source_type=(c or {}).get("source_type", ""),
                    provenance_tier=(c or {}).get("provenance_tier", ""),
                    rights_basis=(c or {}).get("rights_basis", "Pending human confirmation"),
                    simulated_ingest_status="SIMULATED_READY",
                    simulated_chunk_count=chunk_count,
                    source_version_or_date=(c or {}).get("version_or_date", ""),
                )
            )

            if sha:
                artifact_id = _sim_artifact_id(source_id, sha)
                prov_rows.append(
                    ProvenanceRow(
                        source_id=source_id,
                        source_sha256=sha,
                        simulated_artifact_id=artifact_id,
                        inherited_provenance_tier=(c or {}).get("provenance_tier", ""),
                        inherited_rights_basis=(c or {}).get("rights_basis", "Pending human confirmation"),
                        inheritance_mode="deterministic_copy",
                    )
                )

            if size > 0 and sha:
                chunk_rows.extend(build_chunks(source_id, size, sha))

        elif outcome in {"QUARANTINED_PENDING_REVIEW", "ESCALATED"}:
            quarantined_count += 1
            quarantine_rows.append(
                QuarantineRow(
                    source_id=source_id,
                    decision=outcome,
                    quarantine_reason=rationale or "quarantine_or_escalation_required",
                    propagation_action="exclude_from_simulated_ingestion",
                )
            )

        elif outcome == "REJECTED":
            rejected_count += 1
            quarantine_rows.append(
                QuarantineRow(
                    source_id=source_id,
                    decision=outcome,
                    quarantine_reason=rationale or "rejected",
                    propagation_action="exclude_from_simulated_ingestion",
                )
            )

    write_csv(INGESTION_MANIFEST, [asdict(x) for x in approved_rows], list(IngestionRow.__annotations__.keys()))
    write_csv(CHUNK_MANIFEST, [asdict(x) for x in chunk_rows], list(ChunkRow.__annotations__.keys()))
    write_csv(PROVENANCE_MANIFEST, [asdict(x) for x in prov_rows], list(ProvenanceRow.__annotations__.keys()))
    write_csv(QUARANTINE_MANIFEST, [asdict(x) for x in quarantine_rows], list(QuarantineRow.__annotations__.keys()))

    SIM_REPORT.write_text(
        build_report(
            approved=approved_count,
            quarantined=quarantined_count,
            rejected=rejected_count,
            simulated_chunks=len(chunk_rows),
        ),
        encoding="utf-8",
    )

    print("Deterministic ingestion simulation completed.")
    print(f"Approved canonical decisions simulated: {approved_count}")
    print(f"Quarantine/escalation/rejection propagated: {len(quarantine_rows)}")
    print(f"Simulated chunk rows: {len(chunk_rows)}")
    print(f"Ingestion manifest: {INGESTION_MANIFEST}")
    print(f"Chunk manifest: {CHUNK_MANIFEST}")
    print(f"Provenance inheritance manifest: {PROVENANCE_MANIFEST}")
    print(f"Quarantine propagation manifest: {QUARANTINE_MANIFEST}")
    print(f"Simulation report: {SIM_REPORT}")
    print("Boundary preserved: manifests only; no ingestion/indexing/enrichment/activation.")


if __name__ == "__main__":
    main()
