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

LARGE_MIGRATION_MARKER = "CROWN_LARGE_MIGRATION_1887"
LARGE_MIGRATION_TITLE = "refactor(design): complete CROWN visual-system consolidation"
LARGE_MIGRATION_BRANCH = "agent/design-system-1887-final"
LARGE_MIGRATION_ALLOWED_EXACT = {
    ".github/workflows/dashboard-visual-certification.yml",
    ".github/workflows/design-system-1887-evidence-pack.yml",
    "docs/design/CROWN_VISUAL_SYSTEM.md",
    "docs/design/ISSUE_1887_MIGRATION_SUMMARY.json",
    "frontend/dashboards/scripts/check-visual-system.mjs",
    "frontend/dashboards/tests/ui/dashboard-visual-certification.spec.ts",
    "frontend/dashboards/visual-system-baseline.json",
    "scripts/ci/pr_hygiene_gate.py",
}
LARGE_MIGRATION_ALLOWED_PREFIXES = (
    "frontend/dashboards/src/",
)


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


def read_event_pull_request() -> dict[str, object]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).exists():
        return {}
    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return {}
    pull_request = payload.get("pull_request")
    return pull_request if isinstance(pull_request, dict) else {}


def read_event_body(pull_request: dict[str, object]) -> str:
    body = pull_request.get("body")
    return body if isinstance(body, str) else ""


def is_doc_or_audit_only(files: list[FileStat]) -> bool:
    if not files:
        return False
    allowed_prefixes = ("docs/", "audit-artifacts/", ".github/", "scripts/", "tools/")
    return all(f.path.startswith(allowed_prefixes) for f in files)


def is_issue_1887_large_migration(files: list[FileStat], pull_request: dict[str, object], body: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    title = pull_request.get("title")
    head = pull_request.get("head")
    branch = head.get("ref") if isinstance(head, dict) else None

    if LARGE_MIGRATION_MARKER not in body:
        reasons.append(f"missing marker {LARGE_MIGRATION_MARKER}")
    if "Closes #1887" not in body:
        reasons.append("missing issue closure declaration for #1887")
    if title != LARGE_MIGRATION_TITLE:
        reasons.append("pull request title does not match the approved issue #1887 migration title")
    if branch != LARGE_MIGRATION_BRANCH:
        reasons.append("pull request branch does not match the approved issue #1887 migration branch")

    disallowed = []
    for file in files:
        normalized = file.path.replace("\\", "/")
        if normalized in LARGE_MIGRATION_ALLOWED_EXACT:
            continue
        if normalized.startswith(LARGE_MIGRATION_ALLOWED_PREFIXES):
            continue
        disallowed.append(normalized)
    if disallowed:
        reasons.append("disallowed paths in issue #1887 migration: " + ", ".join(sorted(disallowed)))

    return not reasons, reasons


def main() -> int:
    base_ref = os.environ.get("CROWN_BASE_REF", "origin/main")
    files = changed_files(base_ref)
    total_additions = sum(f.additions for f in files)
    total_deletions = sum(f.deletions for f in files)
    threshold = MAX_DOC_AUDIT_ADDITIONS if is_doc_or_audit_only(files) else MAX_NORMAL_ADDITIONS
    failures: list[str] = []
    warnings: list[str] = []

    pull_request = read_event_pull_request()
    body = read_event_body(pull_request)
    large_migration, large_migration_reasons = is_issue_1887_large_migration(files, pull_request, body)

    if len(files) > MAX_CHANGED_FILES and not large_migration:
        failures.append(f"changed file count {len(files)} exceeds limit {MAX_CHANGED_FILES}")
    if total_additions > threshold and not large_migration:
        failures.append(f"added lines {total_additions} exceed limit {threshold}")
    if LARGE_MIGRATION_MARKER in body and not large_migration:
        failures.extend(f"invalid issue #1887 large-migration waiver: {reason}" for reason in large_migration_reasons)

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
    print(f"issue_1887_large_migration={'yes' if large_migration else 'no'}")
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
