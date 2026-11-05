#!/usr/bin/env python3
"""Validate ISO/IEC 27001:2022 Annex A intake integrity, not compliance.

This is a structural and evidence-claim guard. It does not inspect the licensed
standard, assess control applicability, verify evidence, approve management
choices, or represent independent assurance. Never add private audit data here.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTER = ROOT / "docs/compliance/ISO27001_ANNEX_A_SOA_REGISTER_20261028.csv"

COLUMNS = (
    "annex_a_id", "control_family", "normative_title",
    "normative_reference_validation", "applicability",
    "applicability_justification_or_exclusion", "identified_risk_ids",
    "risk_treatment_decision", "implementation_status",
    "proposed_responsible_role", "appointed_control_owner",
    "control_frequency", "evidence_reference", "evidence_stage",
    "operating_test", "findings", "independent_reviewer",
    "management_approval", "review_date", "related_soc2_evidence",
    "next_decision",
)
FAMILIES = ((5, "Organizational", 37), (6, "People", 8),
            (7, "Physical", 14), (8, "Technological", 34))
EXPECTED = {
    f"A.{section}.{index}": family
    for section, family, length in FAMILIES
    for index in range(1, length + 1)
}
APPLICABILITY = {"UNASSESSED", "APPLICABLE", "NOT_APPLICABLE"}
SOURCE_REVIEW = {"PENDING_AUTHORIZED_REVIEW", "AUTHORIZED_REVIEW_COMPLETE"}
IMPLEMENTATION = {
    "NOT_ASSESSED", "NOT_IMPLEMENTED", "PLANNED", "PARTIALLY_IMPLEMENTED",
    "SOURCE_IMPLEMENTED", "RUNTIME_VERIFIED", "OPERATING_VERIFIED",
}
EVIDENCE_STAGE = {"NOT_ASSESSED", "D", "A", "S", "R", "O", "E"}
APPROVAL = {"NOT_APPROVED", "PROPOSED", "APPROVED", "REJECTED"}
PLACEHOLDERS = {
    "", "NONE_LINKED", "UNASSIGNED", "UNMAPPED", "UNDECIDED",
    "NOT_DEFINED", "NOT_ASSESSED", "TO_BE_DEFINED",
    "PENDING_SCOPE_RISK_AND_SOURCE_REVIEW", "REFER_TO_LICENSED_STANDARD",
    "NOT_REVIEWED", "NOT_APPROVED", "PROPOSED", "PENDING", "UNKNOWN",
}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def meaningful(value: str) -> bool:
    return value.strip().upper() not in PLACEHOLDERS


def _date_ok(value: str) -> bool:
    if not DATE.fullmatch(value):
        return False
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_text(content: str) -> list[str]:
    """Return safe, bounded row/field errors without echoing actual cell data."""
    if "\x00" in content:
        return ["file contains a NUL byte"]
    try:
        reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
        header = reader.fieldnames
        if header is None:
            return ["missing CSV header"]
        if tuple(header) != COLUMNS:
            return ["CSV columns must match the approved 21-field intake contract"]
        rows = list(reader)
    except (csv.Error, UnicodeError) as exc:
        return [f"CSV parse error ({type(exc).__name__})"]
    if len(rows) != len(EXPECTED):
        errors = [f"expected 93 Annex A rows, found {len(rows)}"]
    else:
        errors = []
    seen: set[str] = set()
    for number, row in enumerate(rows, 2):
        ident = row.get("annex_a_id") or ""
        label = ident if ident in EXPECTED else f"line {number}"
        if ident in seen:
            errors.append(f"{label}: duplicate annex_a_id")
        seen.add(ident)
        if ident not in EXPECTED:
            errors.append(f"line {number}: unknown Annex A identifier")
        elif row.get("control_family") != EXPECTED[ident]:
            errors.append(f"{label}: control_family does not match Annex A section")
        if None in row or any(not isinstance(value, str) or not value.strip()
                              for value in row.values()):
            errors.append(f"{label}: missing, empty, or extra CSV cell")
            continue
        if any(value.strip().lstrip("' ").startswith(("=", "+", "-", "@"))
               for value in row.values()):
            errors.append(f"{label}: possible spreadsheet formula injection")
        for field, allowed in (
            ("normative_reference_validation", SOURCE_REVIEW),
            ("applicability", APPLICABILITY),
            ("implementation_status", IMPLEMENTATION),
            ("evidence_stage", EVIDENCE_STAGE),
            ("management_approval", APPROVAL),
        ):
            if row[field] not in allowed:
                errors.append(f"{label}: invalid {field} state")
        source = row["normative_reference_validation"]
        applicability = row["applicability"]
        stage = row["evidence_stage"]
        approval = row["management_approval"]
        implementation = row["implementation_status"]
        if source == "AUTHORIZED_REVIEW_COMPLETE":
            if not meaningful(row["independent_reviewer"]):
                errors.append(f"{label}: source validation needs a named reviewer")
            if not _date_ok(row["review_date"]):
                errors.append(f"{label}: source validation needs a valid review date")
            if not meaningful(row["evidence_reference"]):
                errors.append(f"{label}: source validation needs a source-review record")
        if applicability != "UNASSESSED":
            if source != "AUTHORIZED_REVIEW_COMPLETE":
                errors.append(f"{label}: applicability decision requires authorized source review")
            if not meaningful(row["applicability_justification_or_exclusion"]):
                errors.append(f"{label}: applicability decision lacks justification")
            if not meaningful(row["risk_treatment_decision"]):
                errors.append(f"{label}: applicability decision lacks treatment disposition")
        if approval == "APPROVED":
            if applicability == "UNASSESSED":
                errors.append(f"{label}: unassessed control cannot be approved")
            if not meaningful(row["appointed_control_owner"]):
                errors.append(f"{label}: approval requires an appointed owner")
            if not meaningful(row["identified_risk_ids"]):
                errors.append(f"{label}: approval requires linked risk or obligation")
            if not meaningful(row["evidence_reference"]):
                errors.append(f"{label}: approval requires an attributable decision reference")
            if not _date_ok(row["review_date"]):
                errors.append(f"{label}: approval requires a valid review date")
        if implementation in {"PARTIALLY_IMPLEMENTED", "SOURCE_IMPLEMENTED", "RUNTIME_VERIFIED", "OPERATING_VERIFIED"}:
            if not meaningful(row["appointed_control_owner"]):
                errors.append(f"{label}: claimed implementation needs an appointed owner")
            if not meaningful(row["evidence_reference"]):
                errors.append(f"{label}: claimed implementation needs evidence reference")
            if implementation in {"PARTIALLY_IMPLEMENTED", "SOURCE_IMPLEMENTED"} and stage not in {"S", "R", "O", "E"}:
                errors.append(f"{label}: source implementation claim needs verified source evidence stage")
            if implementation == "RUNTIME_VERIFIED" and stage not in {"R", "O", "E"}:
                errors.append(f"{label}: runtime claim needs runtime evidence stage")
            if implementation == "OPERATING_VERIFIED" and stage not in {"O", "E"}:
                errors.append(f"{label}: operating claim needs operating evidence stage")
        if stage in {"S", "R", "O", "E"}:
            if not meaningful(row["evidence_reference"]):
                errors.append(f"{label}: evidence stage needs specific evidence reference")
            if not meaningful(row["operating_test"]):
                errors.append(f"{label}: evidence stage needs a test/verification objective")
            if not _date_ok(row["review_date"]):
                errors.append(f"{label}: evidence stage needs a valid review date")
        if stage in {"O", "E"} and not meaningful(row["findings"]):
            errors.append(f"{label}: operating/assurance claim needs findings disposition")
        if stage == "E" and not meaningful(row["independent_reviewer"]):
            errors.append(f"{label}: independent assurance needs named reviewer")
        if stage == "A" and approval != "APPROVED":
            errors.append(f"{label}: approved evidence stage needs actual management approval")
    missing = EXPECTED.keys() - seen
    if missing:
        errors.append(f"missing {len(missing)} mandatory Annex A identifier(s)")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_REGISTER)
    args = parser.parse_args(argv)
    try:
        if args.path.stat().st_size > 1_000_000:
            print("FAIL: ISO Annex A register exceeds supported size")
            return 1
        contents = args.path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        print("FAIL: ISO Annex A register missing or unreadable")
        return 1
    problems = validate_text(contents)
    if problems:
        print("FAIL: ISO Annex A register integrity")
        for issue in problems[:30]:
            print(f"- {issue}")
        if len(problems) > 30:
            print(f"- {len(problems) - 30} additional finding(s) omitted")
        return 1
    with io.StringIO(contents, newline="") as source:
        rows = list(csv.DictReader(source))
    counts = Counter(row["applicability"] for row in rows)
    print("PASS: 93 unique Annex A identifiers and schema/evidence-claim safeguards")
    print("Applicability decisions (NOT certification): " + ", ".join(
        f"{key}={counts.get(key, 0)}" for key in ("UNASSESSED", "APPLICABLE", "NOT_APPLICABLE")
    ))
    print("NOTE: this validates CSV structure and claim prerequisites only, not control effectiveness, compliance, or independent assurance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
