#!/usr/bin/env python3
"""Fail if hardened workflows stop covering backend/requirements-loadtest.txt."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_WORKFLOWS = {
    ".github/workflows/crown-magus0-gate.yml": [
        "backend/requirements-loadtest.txt",
    ],
    ".github/workflows/dependency-audit.yml": [
        "backend/requirements-loadtest.txt",
    ],
    ".github/workflows/dependency-scan.yml": [
        "requirements-loadtest.txt",
    ],
    ".github/workflows/dependency-integrity-gate.yml": [
        "backend/requirements-loadtest.txt",
    ],
}


def main() -> int:
    violations: list[str] = []

    for rel_path, required_tokens in REQUIRED_WORKFLOWS.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            violations.append(f"missing workflow: {rel_path}")
            continue

        text = path.read_text(encoding="utf-8")
        for token in required_tokens:
            if token not in text:
                violations.append(f"{rel_path} missing required token: {token}")

    if violations:
        print("FAIL: hardened dependency-audit coverage drift detected.\n")
        for violation in violations:
            print(f"- {violation}")
        print(
            "\nRequired workflows must retain backend/requirements-loadtest.txt coverage "
            "to protect release audit fidelity."
        )
        return 1

    print("OK: requirements-loadtest coverage present in hardened workflows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
