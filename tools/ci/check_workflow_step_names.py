#!/usr/bin/env python3
"""
Fail if any workflow name field has an unquoted value containing ': ' (colon-space).

Root cause: GitHub Actions uses go-yaml v3, which treats an unquoted plain
scalar containing ': ' as a mapping indicator. The YAML file fails to parse
and GitHub reports "workflow file issue" — no jobs run, no error surfaced.

Incident: PR #317 introduced guard steps named 'Guard: tag name must match
prod-deploy-*' and 'Guard: tag required and resolvable'. Every prod deploy
from 2026-02-22 onward failed silently until diagnosed and fixed in PR #328.

Rule: any 'name:' value that contains ': ' MUST be wrapped in quotes.

Surface covered:
  - Workflow-level name (column 0):  name: My Workflow: subtitle
  - Job-level name (indented):         name: My Job: subtitle
  - Step-level name (indented):        - name: Guard: check something

False positives: none — quoted values (single or double) are explicitly
allowed through; the check only catches bare unquoted scalars.
Heredoc/inline-script content is unaffected (not matched by these patterns).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Match indented `name:` keys (job-level and step-level):
#   - requires leading whitespace (catches both job name and step name)
#   - value is NOT quoted (doesn't start with " or ')
#   - value contains ': ' (colon-space) anywhere
_INDENTED_NAME = re.compile(
    r"^[ \t]+"          # leading indentation (job/step keys are always indented)
    r"(?:-\s+)?name:"   # optional list indicator, then 'name:'
    r"\s+"              # whitespace after colon
    r"(?![\"'])"        # NOT starting with a quote character
    r"(?P<value>.+)$",  # capture the rest of the line
)

# Match the workflow-level `name:` key (column 0, no indentation).
# This is the top-of-file 'name: My CI Workflow: subtitle' pattern.
_TOPLEVEL_NAME = re.compile(
    r"^name:"           # key at column 0
    r"\s+"              # whitespace after colon
    r"(?![\"'])"        # NOT starting with a quote character
    r"(?P<value>.+)$",  # capture the rest of the line
)

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_TOPLEVEL_NAME, "workflow name"),
    (_INDENTED_NAME, "job/step name"),
]


def check_file(path: Path) -> list[str]:
    violations: list[str] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, label in _PATTERNS:
            m = pattern.match(line)
            if not m:
                continue
            value = m.group("value")
            if ": " in value:
                violations.append(
                    f"  {path.name}:{lineno}: unquoted {label} contains ': '\n"
                    f"    → {line.strip()}\n"
                    f"    Fix: wrap the name in double quotes."
                )
            break  # a line can only match one pattern
    return violations


def main() -> int:
    files = sorted(WORKFLOWS_DIR.glob("*.yml"))
    if not files:
        print("WARNING: no workflow files found", file=sys.stderr)
        return 0

    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))

    if all_violations:
        print("FAIL: unquoted name fields with ': ' found in workflow files.")
        print("These cause 'workflow file issue' on GitHub Actions (no jobs run).\n")
        for v in all_violations:
            print(v)
        print(f"\n{len(all_violations)} violation(s) found.")
        return 1

    print(f"OK: {len(files)} workflow file(s) — no unquoted name fields with ': '")
    return 0


if __name__ == "__main__":
    sys.exit(main())
