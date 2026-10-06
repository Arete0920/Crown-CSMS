#!/usr/bin/env python3
"""
SOLOMON C1 Intake Preprocessor

Purpose:
  Generate C1 candidate review artifacts from local approved source folders.

This script DOES NOT:
  - ingest documents into a corpus
  - index files
  - chunk documents
  - semantically enrich content
  - call an external content service
  - activate retrieval
  - mutate downstream systems

It ONLY:
  - scans local files
  - records metadata
  - computes SHA256 hashes
  - assigns provisional provenance tiers
  - flags review risks
  - creates CSV review queues
  - creates human-readable review packet markdown

Human approval remains required before any future ingestion gate.
"""

from __future__ import annotations

import csv
import hashlib
import mimetypes
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path.cwd()
SOURCE_DIR = ROOT / "c1_candidate_sources"
GOV_DIR = ROOT / "governance" / "c1"
REGISTER_DIR = GOV_DIR / "registers"
REPORT_DIR = GOV_DIR / "reports"
PACKET_DIR = GOV_DIR / "review_packets"

SOURCE_CANDIDATES_CSV = REGISTER_DIR / "source_candidates.csv"
EVIDENCE_REGISTER_CSV = REGISTER_DIR / "evidence_register.csv"
REVIEW_QUEUE_CSV = REGISTER_DIR / "review_queue.csv"
HUMAN_APPROVAL_QUEUE_CSV = REGISTER_DIR / "human_approval_queue.csv"
RISK_EXCEPTIONS_CSV = REGISTER_DIR / "risk_exceptions.csv"
DECISION_REGISTER_CSV = REGISTER_DIR / "decision_register.csv"
READINESS_REPORT = REPORT_DIR / "C1_READINESS_STATUS.md"
REVIEW_PACKET = PACKET_DIR / "C1_REVIEW_PACKET.md"


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".md",
    ".rtf",
    ".json",
    ".yaml",
    ".yml",
    ".png",
    ".jpg",
    ".jpeg",
}

HIGH_RISK_PATTERNS = [
    "ssn",
    "social security",
    "medical",
    "diagnosis",
    "student record",
    "discipline",
    "payroll",
    "bank",
    "routing",
    "account number",
    "password",
    "secret",
    "private key",
    "confidential",
]

OWNED_HINTS = [
    "policy",
    "procedure",
    "handbook",
    "charter",
    "tuition",
    "fee",
    "admission",
    "enrollment",
    "finance",
    "governance",
    "board",
    "contract",
    "agreement",
    "schedule",
]

REFERENCE_HINTS = [
    "template",
    "sample",
    "example",
    "guide",
    "reference",
    "vendor",
    "external",
]


@dataclass
class Candidate:
    source_id: str
    title: str
    source_type: str
    origin_owner: str
    acquisition_method: str
    acquired_by: str
    acquired_at: str
    custody_path: str
    version_or_date: str
    integrity_reference: str
    rights_basis: str
    provenance_tier: str
    review_status: str
    reviewer: str
    decision_date: str
    decision_rationale: str
    risk_flags: str


@dataclass
class Evidence:
    evidence_id: str
    source_id: str
    evidence_type: str
    description: str
    origin: str
    recorded_by: str
    recorded_at: str
    evidence_location: str


@dataclass
class ReviewRow:
    source_id: str
    title: str
    custody_path: str
    sha256: str
    file_size_bytes: int
    source_type: str
    provisional_tier: str
    risk_score: int
    risk_flags: str
    recommended_decision: str
    evidence_gap: str
    human_action_required: str


@dataclass
class RiskException:
    source_id: str
    title: str
    custody_path: str
    risk_score: int
    risk_flags: str
    required_action: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return cleaned[:40] or "SOURCE"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def detect_source_type(path: Path) -> str:
    name = path.name.lower()
    if any(x in name for x in ["policy", "handbook", "charter"]):
        return "policy"
    if any(x in name for x in ["procedure", "process", "sop"]):
        return "procedure"
    if any(x in name for x in ["contract", "agreement", "terms"]):
        return "legal"
    if any(x in name for x in ["tuition", "fee", "payment", "refund", "aid", "finance"]):
        return "operational"
    if any(x in name for x in ["architecture", "technical", "system"]):
        return "technical"
    if path.suffix.lower() in [".csv", ".json", ".xlsx", ".xls"]:
        return "system_export"
    return "reference"


def infer_owner(path: Path) -> str:
    lower_path = str(path).lower()
    if "governance" in lower_path:
        return "Governance Owner"
    if "admission" in lower_path or "enrollment" in lower_path:
        return "Admissions Owner"
    if "finance" in lower_path or "tuition" in lower_path or "fee" in lower_path:
        return "Finance Owner"
    if "legal" in lower_path or "contract" in lower_path:
        return "Legal Owner"
    if "technical" in lower_path or "architecture" in lower_path:
        return "Technical Owner"
    return "Corpus Steward"


def provisional_tier(path: Path) -> str:
    name = path.name.lower()
    full = str(path).lower()

    if any(x in full for x in ["quarantine", "rejected", "unknown"]):
        return "P4"

    if any(x in name for x in REFERENCE_HINTS):
        return "P2"

    if any(x in name for x in OWNED_HINTS):
        return "P1"

    return "P3"


def risk_flags_for(path: Path) -> list[str]:
    flags: list[str] = []
    lower = str(path).lower()

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        flags.append("unsupported_extension")

    if any(pattern in lower for pattern in HIGH_RISK_PATTERNS):
        flags.append("sensitive_or_restricted_hint")

    if any(x in lower for x in ["draft", "old", "obsolete", "deprecated", "archive"]):
        flags.append("deprecated_or_draft_hint")

    if any(x in lower for x in ["unknown", "misc", "unsorted"]):
        flags.append("unknown_origin_hint")

    if path.stat().st_size == 0:
        flags.append("empty_file")

    return flags


def risk_score(flags: list[str], tier: str) -> int:
    score = 0
    score += len(flags) * 20

    if tier == "P3":
        score += 15
    elif tier == "P4":
        score += 50
    elif tier == "P5":
        score += 100

    return min(score, 100)


def recommended_decision(score: int, tier: str, flags: list[str]) -> str:
    if "empty_file" in flags:
        return "REJECTED"
    if score >= 50 or tier in ["P4", "P5"]:
        return "QUARANTINED_PENDING_REVIEW"
    if tier in ["P1", "P2"] and score < 30:
        return "READY_FOR_HUMAN_APPROVAL"
    return "NEEDS_REVIEW"


def evidence_gap(flags: list[str], tier: str) -> str:
    gaps = []

    if tier in ["P2", "P3", "P4"]:
        gaps.append("owner_attestation_required")

    if "unknown_origin_hint" in flags:
        gaps.append("origin_confirmation_required")

    if "deprecated_or_draft_hint" in flags:
        gaps.append("version_supersession_review_required")

    if "sensitive_or_restricted_hint" in flags:
        gaps.append("privacy_security_review_required")

    if "unsupported_extension" in flags:
        gaps.append("format_admissibility_review_required")

    return ";".join(gaps) if gaps else "none"


def human_action(decision: str) -> str:
    if decision == "READY_FOR_HUMAN_APPROVAL":
        return "approve_or_quarantine"
    if decision == "QUARANTINED_PENDING_REVIEW":
        return "resolve_risk_before_approval"
    if decision == "REJECTED":
        return "confirm_rejection"
    return "review_required"


def iter_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []

    ignored_dirs = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "governance",
    }

    files = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        files.append(path)

    return files


def source_id_for(index: int, path: Path) -> str:
    category = "GEN"
    lower = str(path).lower()

    if "governance" in lower:
        category = "GOV"
    elif "admission" in lower or "enrollment" in lower:
        category = "ADM"
    elif "finance" in lower or "tuition" in lower or "fee" in lower:
        category = "FIN"
    elif "legal" in lower or "contract" in lower:
        category = "LEG"
    elif "technical" in lower or "architecture" in lower:
        category = "TECH"

    return f"C1-{category}-{index:04d}"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_packet(review_rows: list[ReviewRow], risk_rows: list[RiskException]) -> str:
    total = len(review_rows)
    ready = sum(1 for r in review_rows if r.recommended_decision == "READY_FOR_HUMAN_APPROVAL")
    quarantine = sum(1 for r in review_rows if r.recommended_decision == "QUARANTINED_PENDING_REVIEW")
    rejected = sum(1 for r in review_rows if r.recommended_decision == "REJECTED")
    needs_review = sum(1 for r in review_rows if r.recommended_decision == "NEEDS_REVIEW")

    lines = [
        "# C1 Human Review Packet",
        "",
        "Generated: deterministic-artifact (runtime metadata intentionally excluded)",
        "",
        "## Boundary Confirmation",
        "",
        "- No ingestion performed",
        "- No indexing performed",
        "- No semantic enrichment performed",
        "- No automation activation performed",
        "- No downstream intelligence workflow performed",
        "",
        "## Summary",
        "",
        f"- Total candidate files: {total}",
        f"- Ready for human approval: {ready}",
        f"- Needs review: {needs_review}",
        f"- Quarantine pending review: {quarantine}",
        f"- Rejected recommendation: {rejected}",
        "",
        "## Human Approval Rule",
        "",
        "No file becomes canonical unless the sole human approver records an explicit decision in decision_register.csv.",
        "",
        "## Ready for Human Approval",
        "",
    ]

    ready_rows = [r for r in review_rows if r.recommended_decision == "READY_FOR_HUMAN_APPROVAL"]

    if not ready_rows:
        lines.append("None.")
    else:
        for row in ready_rows:
            lines.extend(
                [
                    f"### {row.source_id} — {row.title}",
                    "",
                    f"- Path: `{row.custody_path}`",
                    f"- SHA256: `{row.sha256}`",
                    f"- Type: {row.source_type}",
                    f"- Provisional tier: {row.provisional_tier}",
                    f"- Risk score: {row.risk_score}",
                    f"- Risk flags: {row.risk_flags or 'none'}",
                    f"- Recommended action: APPROVE or QUARANTINE",
                    "",
                ]
            )

    lines.extend(["", "## Risk Exceptions", ""])

    if not risk_rows:
        lines.append("None.")
    else:
        for row in risk_rows:
            lines.extend(
                [
                    f"### {row.source_id} — {row.title}",
                    "",
                    f"- Path: `{row.custody_path}`",
                    f"- Risk score: {row.risk_score}",
                    f"- Risk flags: {row.risk_flags}",
                    f"- Required action: {row.required_action}",
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "## Current Readiness",
            "",
            "NO-GO for ingestion.",
            "",
            "Reason: Human approval decisions have not yet been recorded and no ingestion gate has been opened.",
            "",
        ]
    )

    return "\n".join(lines)


def build_readiness_report(review_rows: list[ReviewRow]) -> str:
    approved_count = 0
    if DECISION_REGISTER_CSV.exists():
        with DECISION_REGISTER_CSV.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            approved_count = sum(1 for row in reader if row.get("decision") == "APPROVED_CANONICAL")

    return f"""# C1 Readiness Status

Generated: deterministic-artifact (runtime metadata intentionally excluded)

## Boundary Status

| Control | Status |
|---|---|
| No ingestion | PRESERVED |
| No indexing | PRESERVED |
| No semantic enrichment | PRESERVED |
| No automation activation | PRESERVED |
| No downstream intelligence workflows | PRESERVED |

## Candidate Review Status

| Metric | Count |
|---|---:|
| Candidate files inventoried | {len(review_rows)} |
| Approved canonical decisions recorded | {approved_count} |

## Current Readiness

NO-GO for ingestion.

## Reason

This preprocessor only prepares candidate review materials. It does not authorize ingestion.

C1 remains NO-GO until:
1. the human approver records explicit APPROVED_CANONICAL decisions;
2. risk exceptions are resolved or quarantined;
3. a separate ingestion gate is explicitly opened.
"""


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    REGISTER_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(iter_files(SOURCE_DIR), key=lambda p: str(p).lower())

    candidates: list[Candidate] = []
    evidence: list[Evidence] = []
    review_rows: list[ReviewRow] = []
    risk_rows: list[RiskException] = []

    for index, path in enumerate(files, start=1):
        sid = source_id_for(index, path)
        sha = sha256_file(path)
        rel_path = path.relative_to(ROOT).as_posix()
        observed_at = file_mtime_iso(path)
        flags = risk_flags_for(path)
        tier = provisional_tier(path)
        score = risk_score(flags, tier)
        decision = recommended_decision(score, tier, flags)
        gap = evidence_gap(flags, tier)
        stype = detect_source_type(path)

        risk_text = ";".join(flags)

        candidate = Candidate(
            source_id=sid,
            title=path.stem,
            source_type=stype,
            origin_owner=infer_owner(path),
            acquisition_method="Local approved candidate-source folder scan",
            acquired_by="SOLOMON C1 Intake Preprocessor",
            acquired_at=observed_at,
            custody_path=rel_path,
            version_or_date=observed_at,
            integrity_reference=f"sha256:{sha}",
            rights_basis="Pending human confirmation",
            provenance_tier=tier,
            review_status="NOT_REVIEWED",
            reviewer="",
            decision_date="",
            decision_rationale="",
            risk_flags=risk_text,
        )

        candidates.append(candidate)

        evidence.append(
            Evidence(
                evidence_id=f"EVD-{sid}-HASH",
                source_id=sid,
                evidence_type="HASH_RECORD",
                description=f"SHA256 integrity record for {path.name}",
                origin=rel_path,
                recorded_by="SOLOMON C1 Intake Preprocessor",
                recorded_at=observed_at,
                evidence_location=rel_path,
            )
        )

        review = ReviewRow(
            source_id=sid,
            title=path.stem,
            custody_path=rel_path,
            sha256=sha,
            file_size_bytes=path.stat().st_size,
            source_type=stype,
            provisional_tier=tier,
            risk_score=score,
            risk_flags=risk_text,
            recommended_decision=decision,
            evidence_gap=gap,
            human_action_required=human_action(decision),
        )
        review_rows.append(review)

        if score >= 30 or flags:
            risk_rows.append(
                RiskException(
                    source_id=sid,
                    title=path.stem,
                    custody_path=rel_path,
                    risk_score=score,
                    risk_flags=risk_text,
                    required_action=human_action(decision),
                )
            )

    write_csv(SOURCE_CANDIDATES_CSV, [asdict(x) for x in candidates], list(Candidate.__annotations__.keys()))
    write_csv(EVIDENCE_REGISTER_CSV, [asdict(x) for x in evidence], list(Evidence.__annotations__.keys()))
    write_csv(REVIEW_QUEUE_CSV, [asdict(x) for x in review_rows], list(ReviewRow.__annotations__.keys()))

    approval_rows = [
        asdict(x)
        for x in review_rows
        if x.recommended_decision in ["READY_FOR_HUMAN_APPROVAL", "NEEDS_REVIEW"]
    ]
    write_csv(HUMAN_APPROVAL_QUEUE_CSV, approval_rows, list(ReviewRow.__annotations__.keys()))
    write_csv(RISK_EXCEPTIONS_CSV, [asdict(x) for x in risk_rows], list(RiskException.__annotations__.keys()))

    if not DECISION_REGISTER_CSV.exists():
        write_csv(
            DECISION_REGISTER_CSV,
            [],
            [
                "decision_id",
                "source_id",
                "decision",
                "reviewer",
                "decision_date",
                "rationale",
                "conditions",
            ],
        )

    REVIEW_PACKET.write_text(build_packet(review_rows, risk_rows), encoding="utf-8")
    READINESS_REPORT.write_text(build_readiness_report(review_rows), encoding="utf-8")

    print("C1 intake preprocessor completed.")
    print(f"Candidate source folder: {SOURCE_DIR}")
    print(f"Files inventoried: {len(review_rows)}")
    print(f"Review queue: {REVIEW_QUEUE_CSV}")
    print(f"Human approval queue: {HUMAN_APPROVAL_QUEUE_CSV}")
    print(f"Risk exceptions: {RISK_EXCEPTIONS_CSV}")
    print(f"Review packet: {REVIEW_PACKET}")
    print(f"Readiness report: {READINESS_REPORT}")
    print("Boundary preserved: no ingestion, no indexing, no enrichment, no automation activation.")


if __name__ == "__main__":
    main()
