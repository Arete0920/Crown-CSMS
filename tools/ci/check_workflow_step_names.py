#!/usr/bin/env python3
"""
Fail if any workflow step has an unquoted name containing ': ' (colon-space).

Root cause: GitHub Actions uses go-yaml v3, which treats an unquoted plain
scalar containing ': ' as a mapping indicator. The YAML file fails to parse
and GitHub reports "workflow file issue" — no jobs run, no error surfaced.

Incident: PR #317 introduced guard steps named 'Guard: tag name must match
prod-deploy-*' and 'Guard: tag required and resolvable'. Every prod deploy
from 2026-02-22 onward failed silently until diagnosed and fixed in PR #328.

Rule: any step 'name:' value that contains ': ' MUST be wrapped in quotes.

Pattern matched: lines of the form
    [whitespace]- name: [unquoted value containing ': ']
or
    [whitespace]  name: [unquoted value containing ': ']

False positives: none — quoted values (single or double) are explicitly
allowed through; the check only catches bare unquoted scalars.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Match a `name:` key (as a step key, indented) whose value:
#   - is NOT quoted (doesn't start with " or ')
#   - contains ': ' (colon-space) anywhere
#
# This is the exact YAML construct that causes go-yaml v3 parse failure.
_NAME_LINE = re.compile(
    r"^[ \t]+"          # leading indentation (must be indented — step keys are)
    r"(?:-\s+)?name:"   # optional list indicator, then 'name:'
    r"\s+"              # whitespace after colon
    r"(?![\"'])"        # NOT starting with a quote character
    r"(?P<value>.+)$",  # capture the rest of the line
)


def check_file(path: Path) -> list[str]:
    violations: list[str] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = _NAME_LINE.match(line)
        if not m:
            continue
        value = m.group("value")
        if ": " in value:
            violations.append(
                f"  {path.name}:{lineno}: unquoted step name contains ': '\n"
                f"    → {line.strip()}\n"
                f"    Fix: wrap the name in double quotes."
            )
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
        print("FAIL: unquoted step names with ': ' found in workflow files.")
        print("These cause 'workflow file issue' on GitHub Actions (no jobs run).\n")
        for v in all_violations:
            print(v)
        print(f"\n{len(all_violations)} violation(s) found.")
        return 1

    print(f"OK: {len(files)} workflow file(s) — no unquoted step names with ': '")
    return 0


if __name__ == "__main__":
    sys.exit(main())
