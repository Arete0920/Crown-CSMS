#!/usr/bin/env python3
"""
SOLOMON C1 Corpus Drift Review

Purpose:
    Compare the current policy corpus and simulation artifacts against their
    certified baselines.  Classify every deviation.  Produce a governance
    review report that gates any baseline refresh behind explicit approval.

Rules:
    - NEVER modifies golden_corpus_manifest.csv
    - NEVER modifies baseline_hashes.json
    - NEVER modifies any certification or simulation file
    - NEVER refreshes baselines automatically
    - Exits 0 only when BOTH surfaces show NO_DRIFT
    - Exits 1 when any drift is detected (baseline refresh gated)

Drift surfaces:
    1. SOURCE CORPUS    – c1_candidate_sources/ vs golden_corpus_manifest.csv
    2. ARTIFACT HASHES  – governance/c1 simulation+register artifacts vs
                          governance/c1/determinism/baseline_hashes.json

Drift classification:
    CONTENT_REDUCED       size decreased (potential truncation / deletion)
    CONTENT_EXPANDED      size increased (new content added)
    HASH_CHANGE_SAME_SIZE hash changed but size identical (in-place edit)
    FILE_ADDED            file present in corpus but absent from golden manifest
    FILE_REMOVED          file absent from corpus but present in golden manifest
    ARTIFACT_CHANGED      simulation/register artifact no longer matches baseline

Recommendation levels (per drifted item):
    FLAG_FOR_INVESTIGATION  approved source changed post-approval, or in-place edit
    REVIEW_REQUIRED         change is an expansion; re-approval cycle needed
    QUARANTINE_DRIFT        already-quarantined source has additional drift
    UNREGISTERED_DRIFT      no governance record found for this file
    ARTIFACT_REFRESH_NEEDED simulation artifact baseline is stale (expected after
                             intentional re-run; still requires explicit refresh)

Gate result:
    PASS                    no drift on either surface
    BASELINE_REFRESH_NEEDED artifact hashes are stale but no source corpus drift
    CORPUS_DRIFT_DETECTED   one or more source files deviate from golden state
    INVESTIGATION_REQUIRED  high-suspicion corpus drift requires human review
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "c1"
SIM = GOV / "simulation"
REPORTS = GOV / "reports"

GOLDEN_MANIFEST = GOV / "golden" / "golden_corpus_manifest.csv"
BASELINE_HASHES = GOV / "determinism" / "baseline_hashes.json"
SOURCE_DIR = ROOT / "c1_candidate_sources"
SOURCE_CANDIDATES = GOV / "registers" / "source_candidates.csv"
DECISION_REGISTER = GOV / "registers" / "decision_register.csv"

REPORT_JSON = REPORTS / "C1_CORPUS_DRIFT_REVIEW.json"

# Simulation + register artifacts tracked by the determinism baseline
TRACKED_ARTIFACTS = [
    GOV / "registers" / "source_candidates.csv",
    GOV / "registers" / "evidence_register.csv",
    GOV / "registers" / "review_queue.csv",
    GOV / "registers" / "human_approval_queue.csv",
    GOV / "registers" / "risk_exceptions.csv",
    SIM / "ingestion_simulation_manifest.csv",
    SIM / "chunk_boundary_manifest.csv",
    SIM / "provenance_inheritance_manifest.csv",
    SIM / "quarantine_propagation_manifest.csv",
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel_to_gov(path: Path) -> str:
    return path.relative_to(GOV).as_posix()


def load_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


# ---------------------------------------------------------------------------
# Governance context helpers
# ---------------------------------------------------------------------------

def build_filename_to_source_id() -> dict[str, str]:
    """Map bare filename → source_id using source_candidates custody_path."""
    mapping: dict[str, str] = {}
    for row in load_csv_rows(SOURCE_CANDIDATES):
        custody = row.get("custody_path", "").strip()
        sid = row.get("source_id", "").strip()
        if custody and sid:
            filename = Path(custody).name
            mapping[filename] = sid
    return mapping


def build_source_id_to_decision() -> dict[str, dict]:
    """Map source_id → full decision row."""
    mapping: dict[str, dict] = {}
    for row in load_csv_rows(DECISION_REGISTER):
        sid = row.get("source_id", "").strip()
        if sid:
            mapping[sid] = row
    return mapping


# ---------------------------------------------------------------------------
# Surface 1: Source corpus drift
# ---------------------------------------------------------------------------

def load_golden_manifest() -> dict[str, dict]:
    """Load golden_corpus_manifest.csv; keyed by rel_path (bare filename)."""
    if not GOLDEN_MANIFEST.exists():
        print(f"ERROR: golden manifest missing: {GOLDEN_MANIFEST}", file=sys.stderr)
        sys.exit(2)
    rows = load_csv_rows(GOLDEN_MANIFEST)
    return {r["rel_path"]: r for r in rows}


def current_corpus_state() -> dict[str, dict]:
    """Hash every file in c1_candidate_sources/; keyed by bare filename."""
    out: dict[str, dict] = {}
    if not SOURCE_DIR.exists():
        return out
    for p in sorted(SOURCE_DIR.rglob("*"), key=lambda x: x.name.lower()):
        if p.is_file():
            rel = p.relative_to(SOURCE_DIR).as_posix()
            out[rel] = {
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
    return out


def classify_corpus_drift(
    golden: dict[str, dict],
    current: dict[str, dict],
    filename_to_sid: dict[str, str],
    sid_to_decision: dict[str, dict],
) -> list[dict]:
    all_keys = set(golden) | set(current)
    findings: list[dict] = []

    for rel in sorted(all_keys):
        g = golden.get(rel)
        c = current.get(rel)
        sid = filename_to_sid.get(rel, "")
        decision_row = sid_to_decision.get(sid, {})
        decision = decision_row.get("decision", "NO_DECISION")

        if g is None and c is not None:
            drift_type = "FILE_ADDED"
            size_delta = c["size_bytes"]
            recommendation = (
                "REVIEW_REQUIRED" if sid else "UNREGISTERED_DRIFT"
            )
        elif g is not None and c is None:
            drift_type = "FILE_REMOVED"
            size_delta = -(int(g["size_bytes"]))
            recommendation = (
                "FLAG_FOR_INVESTIGATION"
                if decision == "APPROVED_CANONICAL"
                else "REVIEW_REQUIRED"
            )
        else:
            # Both present — check for hash/size changes
            g_size = int(g["size_bytes"])
            c_size = c["size_bytes"]
            g_sha = g["sha256"]
            c_sha = c["sha256"]

            if g_sha == c_sha and g_size == c_size:
                continue  # identical — no drift

            size_delta = c_size - g_size

            if g_size > c_size:
                drift_type = "CONTENT_REDUCED"
            elif c_size > g_size:
                drift_type = "CONTENT_EXPANDED"
            else:
                drift_type = "HASH_CHANGE_SAME_SIZE"

            if decision == "APPROVED_CANONICAL":
                if drift_type in ("CONTENT_REDUCED", "HASH_CHANGE_SAME_SIZE"):
                    recommendation = "FLAG_FOR_INVESTIGATION"
                else:
                    recommendation = "REVIEW_REQUIRED"
            elif decision == "QUARANTINED_PENDING_REVIEW":
                recommendation = "QUARANTINE_DRIFT"
            else:
                recommendation = "UNREGISTERED_DRIFT"

        entry: dict = {
            "rel_path": rel,
            "source_id": sid or None,
            "governance_decision": decision,
            "drift_type": drift_type,
            "size_delta_bytes": size_delta,
            "recommendation": recommendation,
        }
        if g:
            entry["certified_sha256"] = g["sha256"]
            entry["certified_size_bytes"] = int(g["size_bytes"])
        if c:
            entry["current_sha256"] = c["sha256"]
            entry["current_size_bytes"] = c["size_bytes"]

        findings.append(entry)

    return findings


# ---------------------------------------------------------------------------
# Surface 2: Simulation artifact drift
# ---------------------------------------------------------------------------

def load_baseline_hashes() -> dict[str, str]:
    if not BASELINE_HASHES.exists():
        return {}
    return json.loads(BASELINE_HASHES.read_text(encoding="utf-8"))


def current_artifact_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in TRACKED_ARTIFACTS:
        if p.exists():
            out[rel_to_gov(p)] = sha256_file(p)
    return out


def classify_artifact_drift(
    baseline: dict[str, str],
    current: dict[str, str],
) -> list[dict]:
    findings: list[dict] = []
    all_keys = set(baseline) | set(current)
    for rel in sorted(all_keys):
        b_sha = baseline.get(rel)
        c_sha = current.get(rel)
        if b_sha == c_sha:
            continue
        findings.append({
            "rel_path": rel,
            "drift_type": "ARTIFACT_CHANGED",
            "certified_sha256": b_sha,
            "current_sha256": c_sha,
            "recommendation": "ARTIFACT_REFRESH_NEEDED",
        })
    return findings


# ---------------------------------------------------------------------------
# Gate logic
# ---------------------------------------------------------------------------

def compute_gate(
    corpus_findings: list[dict],
    artifact_findings: list[dict],
) -> str:
    if not corpus_findings and not artifact_findings:
        return "PASS"

    high_suspicion = {
        "FLAG_FOR_INVESTIGATION",
        "QUARANTINE_DRIFT",
        "UNREGISTERED_DRIFT",
    }
    if any(f["recommendation"] in high_suspicion for f in corpus_findings):
        return "INVESTIGATION_REQUIRED"

    if corpus_findings:
        return "CORPUS_DRIFT_DETECTED"

    if artifact_findings:
        return "BASELINE_REFRESH_NEEDED"

    return "PASS"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(report: dict) -> None:
    gate = report["gate_result"]
    ts = report["reviewed_at"]
    print(f"CORPUS DRIFT REVIEW  {ts}")
    print(f"Gate result          {gate}")
    print()

    corpus = report["corpus_drift"]
    print(f"Source corpus        {'NO_DRIFT' if not corpus else str(len(corpus)) + ' file(s) drifted'}")
    for f in corpus:
        print(
            f"  [{f['drift_type']:25s}] {f['rel_path']}"
            f"  source={f['source_id'] or '?':15s}"
            f"  decision={f['governance_decision']}"
            f"  → {f['recommendation']}"
        )

    artifacts = report["artifact_drift"]
    print(f"Simulation artifacts {'NO_DRIFT' if not artifacts else str(len(artifacts)) + ' file(s) drifted'}")
    for f in artifacts:
        print(f"  [{f['drift_type']:25s}] {f['rel_path']}  → {f['recommendation']}")

    print()
    if gate == "PASS":
        print("RESULT: PASS — baselines are current; no action required")
    elif gate == "BASELINE_REFRESH_NEEDED":
        print("RESULT: BASELINE_REFRESH_NEEDED")
        print("  Simulation artifacts have changed since last baseline snapshot.")
        print("  Run verify_c1_artifact_diff.py --refresh after explicit approval.")
    elif gate == "CORPUS_DRIFT_DETECTED":
        print("RESULT: CORPUS_DRIFT_DETECTED")
        print("  One or more policy corpus files differ from certified baseline.")
        print("  Review required before golden corpus manifest may be updated.")
    elif gate == "INVESTIGATION_REQUIRED":
        print("RESULT: INVESTIGATION_REQUIRED  *** BASELINE REFRESH BLOCKED ***")
        print("  High-suspicion drift detected (reduction, in-place edit, or")
        print("  unregistered file).  Human investigation required before any")
        print("  baseline, golden manifest, or certification file may be updated.")
    print()
    print(f"Full report: {REPORT_JSON}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    golden = load_golden_manifest()
    current_corpus = current_corpus_state()
    baseline = load_baseline_hashes()
    current_artifacts = current_artifact_hashes()

    filename_to_sid = build_filename_to_source_id()
    sid_to_decision = build_source_id_to_decision()

    corpus_findings = classify_corpus_drift(
        golden, current_corpus, filename_to_sid, sid_to_decision
    )
    artifact_findings = classify_artifact_drift(baseline, current_artifacts)

    gate = compute_gate(corpus_findings, artifact_findings)

    report = {
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "baseline_refresh_approved": False,
        "corpus_drift": corpus_findings,
        "artifact_drift": artifact_findings,
        "corpus_drift_count": len(corpus_findings),
        "artifact_drift_count": len(artifact_findings),
        "note": (
            "Baseline refresh is GATED. Set baseline_refresh_approved=true only "
            "after explicit governance board sign-off on every finding above."
        ),
    }

    write_json(REPORT_JSON, report)
    print_summary(report)

    return 0 if gate == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
