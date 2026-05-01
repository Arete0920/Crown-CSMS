#!/usr/bin/env python3
"""
Verify closure coverage for the original 215 FAIL remediation rows.

This script validates that each FAIL row in:
  audit-artifacts/51x51-module-integrity/20260428_042020/REMEDIATION_QUEUE/01_FAIL_ROWS.csv
has a corresponding module closure test file under:
  backend/tests/audit_51x51/
with required check-specific tokens.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAIL_CSV = (
    ROOT
    / "audit-artifacts"
    / "51x51-module-integrity"
    / "20260428_042020"
    / "REMEDIATION_QUEUE"
    / "01_FAIL_ROWS.csv"
)
CLOSURE_DIR = ROOT / "backend" / "tests" / "audit_51x51"

CHECK_TOKENS = {
    "23": ["tenant", "cross-tenant", "isolation", "403", "404"],
    "40": ["test_", "pytest"],
    "41": ["APIClient", "request", "response"],
    "42": ["render", "screen", "vitest"],
    "43": ["playwright", "e2e", "spec.ts"],
    "44": ["unauthorized", "invalid", "forbidden", "raises"],
    "46": ["workflow", "pipeline", "gate", "CI"],
    "51": ["Definition of Done Met", "zero FAIL", "zero REVIEW"],
}


def main() -> int:
    if not FAIL_CSV.exists():
        raise FileNotFoundError(f"Missing FAIL CSV: {FAIL_CSV}")
    if not CLOSURE_DIR.exists():
        raise FileNotFoundError(f"Missing closure directory: {CLOSURE_DIR}")

    files = {}
    for p in CLOSURE_DIR.glob("test_51x51_module_*_closure.py"):
        # pattern: test_51x51_module_{id}_{name}_closure.py
        parts = p.stem.split("_")
        try:
            module_id = int(parts[3])
        except (ValueError, IndexError):
            continue
        files[module_id] = p

    rows = list(csv.DictReader(FAIL_CSV.open("r", encoding="utf-8-sig", newline="")))
    open_rows: list[tuple[int, str, str]] = []

    for row in rows:
        module_id = int(row["ModuleId"])
        check_id = str(row["CheckId"])
        file_path = files.get(module_id)

        if not file_path:
            open_rows.append((module_id, check_id, "missing module closure file"))
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        required = CHECK_TOKENS.get(check_id, [])
        if not all(token in text for token in required):
            open_rows.append((module_id, check_id, "missing required check tokens"))

    closed = len(rows) - len(open_rows)
    print(f"queue_fail_rows={len(rows)}")
    print(f"custom_closed_rows={closed}")
    print(f"custom_open_rows={len(open_rows)}")

    if open_rows:
        for module_id, check_id, reason in open_rows[:50]:
            print(f"OPEN module={module_id} check={check_id} reason={reason}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
