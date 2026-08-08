#!/usr/bin/env python3
"""Validate the required CROWN full-module control matrices.

This gate prevents the canonical module completion and review controls from
silently disappearing, omitting rows, using unsupported status vocabulary, or
claiming Certified while independent review remains unassigned.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "docs/product"

REQUIRED_FILES = {
    "completion": PRODUCT / "CROWN_MODULE_COMPLETION_MATRIX.md",
    "ownership": PRODUCT / "CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md",
    "permissions": PRODUCT / "CROWN_MODULE_PERMISSION_MATRIX.md",
    "dashboard_fit": PRODUCT / "CROWN_DASHBOARD_FIT_MATRIX.md",
    "review_raci": PRODUCT / "CROWN_MODULE_REVIEW_RACI.md",
}

CANONICAL_KEYS = [
    "tenant-school-context",
    "identity-users-roles",
    "rbac-permissions",
    "audit-logging",
    "entitlements-subscriptions",
    "retention-rollover",
    "dashboard-certification-contract",
    "school-year-grade",
    "staff-user-role",
    "family-guardian-household",
    "student-master",
    "enrollment-registrar",
    "courses-sections-rosters",
    "attendance",
    "gradebook",
    "transcripts-reportcards",
    "student-care-discipline",
    "admissions",
    "re-enrollment",
    "billing-tuition-ledger",
    "financial-aid",
    "communications",
    "parent-family-portal",
    "teacher-portal",
    "administrator-portal",
    "scheduling",
    "activities-athletics",
    "health-office",
    "transportation",
    "food-service",
    "facilities",
    "safety-security",
    "hr",
    "it-support",
    "fine-arts",
    "library-media",
    "extended-care",
    "summer-camp",
    "spiritual-life",
    "service-outreach-portrait",
    "volunteer-management",
    "advancement-operations",
    "alumni-relations",
    "board-governance",
    "curriculum-pd",
    "network-benchmarking",
    "implementation-success",
    "data-migration",
    "integrations-automation",
    "compliance-audit",
    "revenue-operations",
    "release-reliability",
    "dashboard-certification-center",
]

ALLOWED_STATUSES = {
    "Inventory",
    "Schema-visible",
    "Wired",
    "Runtime-visible",
    "Evidence-backed",
    "Certified",
}

failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)


for label, path in REQUIRED_FILES.items():
    if not path.exists():
        fail(f"missing required {label} control: {path.relative_to(ROOT)}")

if failures:
    for item in failures:
        print(f"FAIL: {item}")
    raise SystemExit(1)

completion = REQUIRED_FILES["completion"].read_text(encoding="utf-8-sig")
raci = REQUIRED_FILES["review_raci"].read_text(encoding="utf-8-sig")

completion_rows: dict[str, str] = {}
for line in completion.splitlines():
    match = re.match(r"^\|\s*[^|]+\|\s*`([^`]+)`\s*\|\s*[^|]+\|\s*([^|]+?)\s*\|", line)
    if not match:
        continue
    key, status = match.groups()
    if key in CANONICAL_KEYS:
        if key in completion_rows:
            fail(f"duplicate completion row: {key}")
        completion_rows[key] = status.strip()

missing_completion = [key for key in CANONICAL_KEYS if key not in completion_rows]
extra_completion = sorted(set(completion_rows) - set(CANONICAL_KEYS))
if missing_completion:
    fail(f"completion matrix missing canonical rows: {missing_completion}")
if extra_completion:
    fail(f"completion matrix contains unexpected rows: {extra_completion}")

for key, status in completion_rows.items():
    if status not in ALLOWED_STATUSES:
        fail(f"completion row {key} uses unsupported status: {status}")

raci_reviewers: dict[str, str] = {}
for line in raci.splitlines():
    match = re.match(r"^\|\s*[^|]+\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|", line)
    if not match:
        continue
    key, reviewer = match.groups()
    if key in CANONICAL_KEYS:
        if key in raci_reviewers:
            fail(f"duplicate RACI row: {key}")
        raci_reviewers[key] = reviewer.strip()

missing_raci = [key for key in CANONICAL_KEYS if key not in raci_reviewers]
if missing_raci:
    fail(f"review RACI missing canonical rows: {missing_raci}")

for key, status in completion_rows.items():
    if status == "Certified" and raci_reviewers.get(key, "UNASSIGNED").upper() == "UNASSIGNED":
        fail(f"{key} is Certified while independent reviewer remains UNASSIGNED")

if len(completion_rows) != 53:
    fail(f"completion matrix row count is {len(completion_rows)}; expected 53")
if len(raci_reviewers) != 53:
    fail(f"review RACI row count is {len(raci_reviewers)}; expected 53")

if failures:
    for item in failures:
        print(f"FAIL: {item}")
    raise SystemExit(1)

certified = sum(1 for status in completion_rows.values() if status == "Certified")
unassigned = sum(1 for reviewer in raci_reviewers.values() if reviewer.upper() == "UNASSIGNED")
print("PASS: required module control matrices are present and structurally aligned.")
print(f"PASS: canonical completion rows={len(completion_rows)} certified={certified}.")
print(f"PASS: canonical RACI rows={len(raci_reviewers)} unassigned_reviewers={unassigned}.")
