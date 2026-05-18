#!/usr/bin/env python3
"""Verify current candidate sources against frozen golden corpus manifest."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "c1_candidate_sources"
MANIFEST = ROOT / "governance" / "c1" / "golden" / "golden_corpus_manifest.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST.exists():
        _fail(f"golden manifest missing: {MANIFEST}")
    with MANIFEST.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r["rel_path"]: r for r in rows}


def current_files() -> dict[str, dict[str, str]]:
    files = sorted([p for p in SOURCE_DIR.rglob("*") if p.is_file()], key=lambda p: str(p).lower())
    out: dict[str, dict[str, str]] = {}
    for p in files:
        rel = p.relative_to(SOURCE_DIR).as_posix()
        out[rel] = {
            "size_bytes": str(p.stat().st_size),
            "sha256": sha256(p),
        }
    return out


def main() -> None:
    expected = load_manifest()
    actual = current_files()

    expected_keys = set(expected)
    actual_keys = set(actual)

    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)

    if missing:
        _fail("missing files from golden corpus:\n- " + "\n- ".join(missing))
    if extra:
        _fail("unexpected extra files vs golden corpus:\n- " + "\n- ".join(extra))

    mismatches = []
    for rel, exp in expected.items():
        act = actual[rel]
        if act["size_bytes"] != exp["size_bytes"] or act["sha256"] != exp["sha256"]:
            mismatches.append(rel)

    if mismatches:
        _fail("golden corpus drift detected:\n- " + "\n- ".join(mismatches))

    _ok("golden corpus verification passed (file set and hashes identical)")


if __name__ == "__main__":
    main()
