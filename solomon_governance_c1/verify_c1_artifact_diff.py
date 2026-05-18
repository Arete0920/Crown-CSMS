#!/usr/bin/env python3
"""Cryptographic artifact diff verification for deterministic C1 runs.

Compares required deterministic artifacts between current run and baseline snapshot.
If no baseline exists, creates one explicitly (bootstrap mode).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "c1"
DET = GOV / "determinism"
BASELINE_DIR = DET / "baseline"
BASELINE_HASH = DET / "baseline_hashes.json"

ARTIFACTS = [
    GOV / "registers" / "source_candidates.csv",
    GOV / "registers" / "evidence_register.csv",
    GOV / "registers" / "review_queue.csv",
    GOV / "registers" / "human_approval_queue.csv",
    GOV / "registers" / "risk_exceptions.csv",
    GOV / "simulation" / "ingestion_simulation_manifest.csv",
    GOV / "simulation" / "chunk_boundary_manifest.csv",
    GOV / "simulation" / "provenance_inheritance_manifest.csv",
    GOV / "simulation" / "quarantine_propagation_manifest.csv",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(GOV).as_posix()


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def ensure_artifacts() -> None:
    missing = [rel(p) for p in ARTIFACTS if not p.exists()]
    if missing:
        _fail("missing artifacts:\n- " + "\n- ".join(missing))


def current_hashes() -> dict[str, str]:
    return {rel(p): sha256(p) for p in ARTIFACTS}


def write_baseline(hashes: dict[str, str]) -> None:
    if BASELINE_DIR.exists():
        shutil.rmtree(BASELINE_DIR)
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)

    for p in ARTIFACTS:
        target = BASELINE_DIR / rel(p)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)

    BASELINE_HASH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_HASH.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_baseline() -> dict[str, str]:
    if not BASELINE_HASH.exists():
        return {}
    return json.loads(BASELINE_HASH.read_text(encoding="utf-8"))


def compare(cur: dict[str, str], base: dict[str, str]) -> None:
    if set(cur) != set(base):
        _fail("artifact keyset mismatch between current and baseline")

    changed = []
    for k in sorted(cur):
        if cur[k] != base[k]:
            changed.append(k)

    if changed:
        lines = ["cryptographic drift detected:"]
        for k in changed:
            lines.append(f"- {k}")
        _fail("\n".join(lines))

    _ok("all required artifacts are byte-identical to baseline")


def main() -> None:
    ensure_artifacts()
    cur = current_hashes()
    base = load_baseline()

    if not base:
        write_baseline(cur)
        _ok("baseline snapshot created (bootstrap)")
        return

    compare(cur, base)


if __name__ == "__main__":
    main()
