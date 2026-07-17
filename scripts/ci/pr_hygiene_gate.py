#!/usr/bin/env python3
"""CROWN PR hygiene gate.

This gate prevents generated artifact noise, oversized diffs, stale evidence dumps,
and invalid solo-developer governance language from becoming normal PR flow.
It is intentionally conservative: merge discussion starts only after hygiene is clean.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_NORMAL_ADDITIONS = int(os.environ.get("CROWN_MAX_NORMAL_ADDITIONS", "1500"))
MAX_DOC_AUDIT_ADDITIONS = int(os.environ.get("CROWN_MAX_DOC_AUDIT_ADDITIONS", "3000"))
MAX_CHANGED_FILES = int(os.environ.get("CROWN_MAX_CHANGED_FILES", "20"))

FORBIDDEN_GENERATED_PATTERNS = [
    re.compile(r"^audit-artifacts/.+/(dashboard_truth|widget_truth|pr_truth|evidence_inventory)\.json$"),
    re.compile(r"^audit-artifacts/.+/(widget_truth|pr_truth|evidence_inventory)\.md$"),
    re.compile(r"^audit-artifacts/.+/(playwright-report|test-results|traces|screenshots)(/|$)"),
    re.compile(r"^.*\.(tmp|bak|swp|log)$"),
]

STALE_EVIDENCE_PATTERNS = [
    re.compile(r"^docs/release/evidence/live-pack/\d{8}_\d{6}/"),
    re.compile(r"^audit-artifacts/.+/\d{8}_\d{6}/"),
]

GENERATED_EXTENSIONS = {".json", ".ndjson", ".csv", ".log"}
SUMMARY_ALLOWLIST = {
    "audit-artifacts/dashboard-certification-truth/closeout_plan.md",
}


@dataclass
class FileStat:
    status: str
    additions: int
    deletions: int
    path: str


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def changed_files(base_ref: str) -> list[FileStat]:
    out = run(["git", "diff", "--numstat", "--diff-filter=ACMR", f"{base_ref}...HEAD"])
    rows: list[FileStat] = []
    if not out:
        return rows
    status_out = run(["git", "diff", "--name-status", "--diff-filter=ACMR", f"{base_ref}...HEAD"])
    status_by_path: dict[str, str] = {}
    for line in status_out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status_by_path[parts[-1]] = parts[0]
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add_raw, del_raw, path = parts[0], parts[1], parts[2]
        additions = 0 if add_raw == "-" else int(add_raw)
        deletions = 0 if del_raw == "-" else int(del_raw)
        rows.append(FileStat(status=status_by_path.get(path, "?"), additions=additions, deletions=deletions, path=path))
    return rows


def read_event_body() -> str:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).exists():
        return ""

    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return ""

    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return ""

    body = pull_request.get("body")
    return body if isinstance(body, str) else ""


def is_doc_or_audit_only(files: list[FileStat]) -> bool:
    if not files:
        return False
    allowed_prefixes = ("docs/", "audit-artifacts/", ".github/", "scripts/", "tools/")
    return all(f.path.startswith(allowed_prefixes) for f in files)


def main() -> int:
    base_ref = os.environ.get("CROWN_BASE_REF", "origin/main")
    files = changed_files(base_ref)
    total_additions = sum(f.additions for f in files)
    total_deletions = sum(f.deletions for f in files)
    threshold = MAX_DOC_AUDIT_ADDITIONS if is_doc_or_audit_only(files) else MAX_NORMAL_ADDITIONS
    failures: list[str] = []
    warnings: list[str] = []

    if len(files) > MAX_CHANGED_FILES:
        failures.append(f"changed file count {len(files)} exceeds limit {MAX_CHANGED_FILES}")

    if total_additions > threshold:
        failures.append(f"added lines {total_additions} exceed limit {threshold}")

    for f in files:
        normalized = f.path.replace("\\", "/")
        if normalized not in SUMMARY_ALLOWLIST:
            for pattern in FORBIDDEN_GENERATED_PATTERNS:
                if pattern.search(normalized):
                    failures.append(f"forbidden generated artifact committed: {normalized}")
                    break
        for pattern in STALE_EVIDENCE_PATTERNS:
            if pattern.search(normalized):
                failures.append(f"timestamped/stale evidence path committed: {normalized}")
                break
        if Path(normalized).suffix.lower() in GENERATED_EXTENSIONS and normalized.startswith("audit-artifacts/"):
            warnings.append(f"generated audit data file requires explicit justification or artifact upload instead: {normalized}")

    body = read_event_body()
    if "INDEPENDENT_REVIEW_REQUIRED" in body and "SOLO_DEVELOPER_APPROVED_WORKAROUND" not in body:
        failures.append("PR body waits for independent review without solo-developer workaround control path")

    if "SOLO_DEVELOPER_APPROVED_WORKAROUND" in body and "ChatGPT" in body and "approval authority" not in body:
        failures.append("solo-developer workaround language must state ChatGPT is not approval authority")

    print("# CROWN PR Hygiene Gate")
    print(f"base_ref={base_ref}")
    print(f"changed_files={len(files)}")
    print(f"additions={total_additions}")
    print(f"deletions={total_deletions}")
    print(f"addition_limit={threshold}")
    print("")
    print("## Changed files")
    for f in files:
        print(f"- {f.status} +{f.additions}/-{f.deletions} {f.path}")

    if warnings:
        print("")
        print("## Warnings")
        for warning in warnings:
            print(f"- WARNING: {warning}")

    if failures:
        print("")
        print("## Verdict")
        print("NO-GO")
        print("")
        print("## Failures")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("")
    print("## Verdict")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
