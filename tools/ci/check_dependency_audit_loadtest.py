#!/usr/bin/env python3
"""Fail if the canonical dependency audit stops covering load-test requirements."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_WORKFLOWS = {
    ".github/workflows/dependency-audit.yml": [
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
        print("FAIL: canonical dependency-audit coverage drift detected.\n")
        for violation in violations:
            print(f"- {violation}")
        print(
            "\nThe retained dependency audit must cover "
            "backend/requirements-loadtest.txt to protect release audit fidelity."
        )
        return 1

    print("OK: load-test requirements coverage present in canonical dependency audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
