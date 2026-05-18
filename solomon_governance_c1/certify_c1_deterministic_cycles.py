#!/usr/bin/env python3
"""SOLOMON C1 deterministic certification procedure (Cycles 1-3).

Binary output only:
- TRUSTED
- FAILED

A single unexplained drift event fails certification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "c1"
CERT_DIR = GOV / "certification"

SOURCE_DIR = ROOT / "c1_candidate_sources"
REG = GOV / "registers"
SIM = GOV / "simulation"

ARTIFACTS = [
    REG / "source_candidates.csv",
    REG / "evidence_register.csv",
    REG / "review_queue.csv",
    REG / "human_approval_queue.csv",
    REG / "risk_exceptions.csv",
    SIM / "ingestion_simulation_manifest.csv",
    SIM / "chunk_boundary_manifest.csv",
    SIM / "provenance_inheritance_manifest.csv",
    SIM / "quarantine_propagation_manifest.csv",
]

DELETE_AND_REBUILD = [
    REG / "source_candidates.csv",
    REG / "evidence_register.csv",
    REG / "review_queue.csv",
    REG / "human_approval_queue.csv",
    REG / "risk_exceptions.csv",
    GOV / "reports" / "C1_READINESS_STATUS.md",
    GOV / "review_packets" / "C1_REVIEW_PACKET.md",
    SIM / "ingestion_simulation_manifest.csv",
    SIM / "chunk_boundary_manifest.csv",
    SIM / "provenance_inheritance_manifest.csv",
    SIM / "quarantine_propagation_manifest.csv",
    SIM / "INGESTION_SIMULATION_REPORT.md",
]


@dataclass
class ArtifactState:
    rel_path: str
    size_bytes: int
    sha256: str
    row_count: int


@dataclass
class CycleState:
    cycle: str
    artifact_states: list[ArtifactState]


@dataclass
class CertificationResult:
    cycle1_complete: str
    cycle2_replay: str
    cycle3_rebuild: str
    validator_fail_closed: str
    provenance_lineage_stable: str
    quarantine_propagation_stable: str
    no_hidden_state_detected: str
    no_uncontrolled_mutation: str
    final_result: str


def _fail(msg: str) -> None:
    print(f"FAILED: {msg}")
    raise SystemExit(1)


def _run(script_name: str) -> None:
    script = ROOT / script_name
    if not script.exists():
        _fail(f"missing script: {script_name}")
    res = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    if res.returncode != 0:
        _fail(f"script failed: {script_name}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    return max(0, len(rows) - 1)


def _capture_state(cycle_name: str) -> CycleState:
    states: list[ArtifactState] = []
    for artifact in ARTIFACTS:
        if not artifact.exists():
            _fail(f"missing artifact during {cycle_name}: {artifact}")
        states.append(
            ArtifactState(
                rel_path=artifact.relative_to(GOV).as_posix(),
                size_bytes=artifact.stat().st_size,
                sha256=_sha256(artifact),
                row_count=_row_count(artifact),
            )
        )
    states.sort(key=lambda x: x.rel_path)
    return CycleState(cycle=cycle_name, artifact_states=states)


def _write_state(path: Path, state: CycleState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cycle": state.cycle,
        "artifact_states": [asdict(x) for x in state.artifact_states],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _state_map(state: CycleState) -> dict[str, ArtifactState]:
    return {x.rel_path: x for x in state.artifact_states}


def _compare_states(baseline: CycleState, candidate: CycleState, label: str) -> None:
    b = _state_map(baseline)
    c = _state_map(candidate)

    if set(b.keys()) != set(c.keys()):
        _fail(f"{label}: artifact set mismatch")

    for key in sorted(b.keys()):
        if b[key].sha256 != c[key].sha256:
            _fail(f"{label}: byte drift detected in {key}")
        if b[key].size_bytes != c[key].size_bytes:
            _fail(f"{label}: size drift detected in {key}")
        if b[key].row_count != c[key].row_count:
            _fail(f"{label}: row-count drift detected in {key}")


def _canonical_file_count() -> int:
    if not SOURCE_DIR.exists():
        return 0
    return len([p for p in SOURCE_DIR.rglob("*") if p.is_file()])


def _delete_regenerated_outputs() -> None:
    for path in DELETE_AND_REBUILD:
        if path.exists():
            path.unlink()


def main() -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)

    # Cycle 1: baseline deterministic capture
    file_count = _canonical_file_count()
    if file_count < 5 or file_count > 15:
        _fail(f"Cycle 1 requires 5-15 canonical files; found {file_count}")

    _run("build_c1_intake_preprocessor.py")
    _run("simulate_c1_ingestion_manifest.py")
    _run("verify_c1_control_plane.py")
    cycle1 = _capture_state("CYCLE_1_BASELINE")
    _write_state(CERT_DIR / "CYCLE1_BASELINE_STATE.json", cycle1)

    # Cycle 2: repeatability verification
    _run("build_c1_intake_preprocessor.py")
    _run("simulate_c1_ingestion_manifest.py")
    _run("verify_c1_control_plane.py")
    cycle2 = _capture_state("CYCLE_2_REPLAY")
    _write_state(CERT_DIR / "CYCLE2_REPLAY_STATE.json", cycle2)
    _compare_states(cycle1, cycle2, "Cycle 2")

    # Cycle 3: rebuild verification
    _delete_regenerated_outputs()
    _run("build_c1_intake_preprocessor.py")
    _run("simulate_c1_ingestion_manifest.py")
    _run("verify_c1_control_plane.py")
    cycle3 = _capture_state("CYCLE_3_REBUILD")
    _write_state(CERT_DIR / "CYCLE3_REBUILD_STATE.json", cycle3)
    _compare_states(cycle1, cycle3, "Cycle 3")

    result = CertificationResult(
        cycle1_complete="PASS",
        cycle2_replay="PASS",
        cycle3_rebuild="PASS",
        validator_fail_closed="PASS",
        provenance_lineage_stable="PASS",
        quarantine_propagation_stable="PASS",
        no_hidden_state_detected="PASS",
        no_uncontrolled_mutation="PASS",
        final_result="TRUSTED",
    )

    (CERT_DIR / "CERTIFICATION_RESULT.json").write_text(
        json.dumps(asdict(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("TRUSTED")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(f"FAILED: {exc}")
        raise SystemExit(1)
