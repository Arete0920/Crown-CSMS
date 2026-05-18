#!/usr/bin/env python3
"""Freeze current candidate sources as the golden corpus benchmark."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "c1_candidate_sources"
GOLDEN_DIR = ROOT / "governance" / "c1" / "golden"
MANIFEST = GOLDEN_DIR / "golden_corpus_manifest.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def iter_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted([p for p in base.rglob("*") if p.is_file()], key=lambda p: str(p).lower())


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    files = iter_files(SOURCE_DIR)

    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["rel_path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        for p in files:
            writer.writerow(
                {
                    "rel_path": p.relative_to(SOURCE_DIR).as_posix(),
                    "size_bytes": p.stat().st_size,
                    "sha256": sha256(p),
                }
            )

    print(f"Golden corpus manifest frozen: {MANIFEST}")
    print(f"File count: {len(files)}")


if __name__ == "__main__":
    main()
