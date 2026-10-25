"""Cached repository inventory for existing module-source smoke contracts.

Tests run on a fixed source checkout. Cache the full Python source inventory
once per pytest process; retain original file count, decoding and error behavior.
No assertions or required coverage thresholds are removed.
"""
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def source_inventory() -> tuple[int, str]:
    paths = list(PROJECT_ROOT.rglob("*.py"))
    chunks = []
    for path in paths:
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
    return len(paths), "".join(chunks)
