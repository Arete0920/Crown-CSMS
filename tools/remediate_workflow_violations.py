#!/usr/bin/env python3
"""Automated remediation for workflow policy violations.

Fixes:
  1. Missing top-level concurrency block
  2. Missing timeout-minutes on jobs
  3. curl commands missing --max-time / -f
  4. Mojibake / non-clean text sequences (strip offending chars)
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF_DIR = ROOT / ".github" / "workflows"

MOJIBAKE_RE = re.compile(r"[âΓœ†œ©\x80-\x9f\ufffd]")


# ---------------------------------------------------------------------------
# 1. Concurrency block
# ---------------------------------------------------------------------------
CONCURRENCY_BLOCK_TEMPLATE = """\
concurrency:
  group: {group}-${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: false
"""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def fix_concurrency(text: str, filename: str) -> str:
    if re.search(r"(?m)^concurrency:\s*$", text):
        return text  # already present

    name_match = re.search(r"(?m)^name:\s*(.+?)\s*$", text)
    slug = _slug(name_match.group(1)) if name_match else _slug(filename.replace(".yml", ""))
    block = CONCURRENCY_BLOCK_TEMPLATE.format(group=slug)

    # Insert before `jobs:` line
    return re.sub(r"(?m)^(jobs:\s*$)", block + r"\1", text, count=1)


# ---------------------------------------------------------------------------
# 2. Timeout-minutes on jobs
# ---------------------------------------------------------------------------
JOB_HEADER_RE = re.compile(
    r"(?m)^  ([A-Za-z0-9_-]+):\s*\n((?:    [^\n]*\n)*?)(    runs-on:)",
)
TIMEOUT_LINE = "    timeout-minutes: 30\n"


def fix_timeouts(text: str) -> str:
    """Add timeout-minutes: 30 to any job that lacks it, right after runs-on."""

    def add_timeout(m: re.Match) -> str:
        job_body_before = m.group(2)
        runs_on_line = m.group(3)
        full = m.group(0)
        # If timeout already exists in this job's leading block, skip
        if "timeout-minutes:" in job_body_before:
            return full
        # Find the runs-on line end and insert timeout after it
        after_runs_on = re.sub(
            r"(    runs-on:[^\n]*\n)",
            r"\1" + TIMEOUT_LINE,
            full,
            count=1,
        )
        return after_runs_on

    return JOB_HEADER_RE.sub(add_timeout, text)


def fix_timeouts_v2(text: str) -> str:
    """Parse jobs block and add timeout-minutes after runs-on where missing."""
    lines = text.splitlines(keepends=True)
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)
        # Detect a job's runs-on line (4-space indent)
        if re.match(r"^    runs-on:", line):
            # Look ahead: is the next non-blank line already a timeout?
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                result.append(lines[j])
                j += 1
            if j < len(lines) and "timeout-minutes:" in lines[j]:
                pass  # already has it, skip
            else:
                result.append(TIMEOUT_LINE)
            i = j
            continue
        i += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# 3. curl safety fixes
# ---------------------------------------------------------------------------
def _fix_curl_line(cmd_line: str) -> str:
    """Add -f and --max-time 30 to a curl invocation if missing.

    Status-probe curls (-w "%{http_code}") are exempt from -f but still need --max-time.
    """
    modified = cmd_line
    explicit_status_probe = "%{http_code}" in modified or "-w " in modified

    if not explicit_status_probe:
        if "-f" not in modified and "--fail" not in modified and "-fsS" not in modified:
            modified = re.sub(r"\bcurl\b", "curl -f", modified, count=1)

    if "--max-time" not in modified and "--connect-timeout" not in modified:
        modified = re.sub(r"\bcurl\b", "curl --max-time 30", modified, count=1)

    return modified


def fix_curl(text: str) -> str:
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "curl " not in line or line.strip().startswith("#"):
            result.append(line)
            i += 1
            continue

        # Gather continuation lines
        chunk = [line]
        while chunk[-1].rstrip("\n").endswith("\\") and i + 1 < len(lines):
            i += 1
            chunk.append(lines[i])

        full_cmd = "".join(chunk)
        fixed_cmd = _fix_curl_line(full_cmd)
        result.append(fixed_cmd)
        i += 1
        continue

    return "".join(result)


# ---------------------------------------------------------------------------
# 4. Mojibake removal
# ---------------------------------------------------------------------------
def fix_mojibake(text: str) -> str:
    return MOJIBAKE_RE.sub("", text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def remediate(path: pathlib.Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    text = original

    text = fix_mojibake(text)
    text = fix_concurrency(text, path.name)
    text = fix_timeouts_v2(text)
    text = fix_curl(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    targets = [pathlib.Path(p).resolve() for p in sys.argv[1:]]
    files = targets if targets else sorted(WF_DIR.glob("*.yml"))
    changed = 0
    for wf in files:
        if not wf.exists():
            continue
        if remediate(wf):
            print(f"  fixed: {wf.name}")
            changed += 1
        else:
            print(f"  clean: {wf.name}")
    print(f"\n{changed} file(s) modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
