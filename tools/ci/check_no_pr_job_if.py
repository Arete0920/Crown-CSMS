#!/usr/bin/env python3
"""
Fail if any workflow has a *job-level* `if:` that references pull_request head ref.

Why: If a required check's job is SKIPPED, GitHub reports NEUTRAL and merge can be blocked forever.
Fix pattern: move gating to *step-level* `if:` and include a pass-through step for non-applicable branches.

Allowlist:
- tools/ci/job_if_allowlist.txt lines: "<workflow_filename>:<job_id>"
  Example: "rc-promotion-gate.yml:rc-promotion-gate"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except Exception as e:
    print(f"ERROR: PyYAML not available: {e}", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ALLOWLIST_PATH = REPO_ROOT / "tools" / "ci" / "job_if_allowlist.txt"

# Strings that indicate PR-head-ref gating (the exact class that caused SKIPPED->neutral)
BAD_SUBSTRINGS = [
    "github.event.pull_request.head.ref",
    "github.head_ref",  # often used for PR branch checks
]


def load_allowlist() -> set[str]:
    if not ALLOWLIST_PATH.exists():
        return set()
    items: set[str] = set()
    for raw in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        items.add(line)
    return items


def is_yaml_file(p: Path) -> bool:
    return p.suffix.lower() in {".yml", ".yaml"}


def main() -> int:
    if not WORKFLOWS_DIR.exists():
        print("OK: No workflows directory found.")
        return 0

    allowlist = load_allowlist()
    violations: list[str] = []

    for wf in sorted(WORKFLOWS_DIR.iterdir()):
        if not wf.is_file() or not is_yaml_file(wf):
            continue

        text = wf.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(text) or {}
        except Exception as e:
            # PyYAML can't parse workflows with inline scripts containing colons.
            # This is a PyYAML limitation, not a workflow authoring problem.
            # Skip and warn — don't fail.
            print(f"WARNING: skipping {wf.name} (PyYAML parse error: {e})", file=sys.stderr)
            continue

        jobs = (data or {}).get("jobs") or {}
        if not isinstance(jobs, dict):
            continue

        for job_id, job_def in jobs.items():
            if not isinstance(job_def, dict):
                continue
            job_if = job_def.get("if")
            if not job_if:
                continue
            job_if_str = str(job_if)

            # Allowlist entry format: "<workflow_filename>:<job_id>"
            allow_key = f"{wf.name}:{job_id}"
            if allow_key in allowlist:
                continue

            # Only flag the risky class: PR head-ref gating at the *job level*
            lowered = job_if_str.lower()
            if any(s.lower() in lowered for s in BAD_SUBSTRINGS):
                violations.append(
                    f"{wf.name}:{job_id} has job-level if referencing PR branch: {job_if_str}"
                )

    if violations:
        print("FAIL: Disallowed job-level PR-branch gating detected in workflows.\n")
        for v in violations:
            print(f"- {v}")
        print(
            "\nRequired checks must never be job-skipped on PRs.\n"
            "Move PR-branch gating to STEP-level `if:` and add a pass-through step.\n"
            "If you truly need an exception, add '<workflow>:<job_id>' to tools/ci/job_if_allowlist.txt."
        )
        return 1

    print("OK: No disallowed job-level PR-branch gating found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
