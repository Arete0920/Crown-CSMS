#!/usr/bin/env python3
"""
SOLOMON C1 Governance Kit Builder

Purpose:
  Build a pre-ingestion governance review package for Corpus C1.

Hard constraints:
  - No ingestion
  - No indexing
  - No semantic enrichment
  - No automation activation
  - No downstream intelligence workflows

Outputs:
  governance/c1/
    00_BOUNDARY.md
    01_CANONICAL_SOURCE_ACCEPTANCE_CRITERIA.md
    02_PROVENANCE_TAXONOMY.md
    03_CHAIN_OF_CUSTODY_STANDARD.md
    04_EVIDENCE_ADMISSIBILITY_RULES.md
    05_REVIEW_CHECKLIST.md
    06_APPROVAL_MATRIX.md
    07_QUARANTINE_AND_REVOCATION.md
    schemas/
      source_candidate.schema.json
      evidence_record.schema.json
      review_decision.schema.json
    registers/
      source_candidates.csv
      evidence_register.csv
      decision_register.csv
    reports/
      C1_READINESS_STATUS.md
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("governance/c1")


BOUNDARY = """# C1 Governance Boundary

Status: PAUSED / GOVERNANCE-FIRST

This package supports manual Corpus C1 canonical-source acquisition review only.

## Authorized Activities

- Define source acceptance criteria
- Classify provenance
- Record evidence metadata
- Review candidate sources
- Record approval, rejection, quarantine, or escalation decisions
- Preserve chain-of-custody documentation

## Explicitly Prohibited Activities

- No ingestion
- No indexing
- No semantic enrichment
- No automation activation
- No downstream intelligence workflows
- No production corpus mutation
- No model-facing retrieval activation

## Gate Condition

The next valid operational transition is:

Corpus C1 Manual Canonical-Source Acquisition Review

No source may advance beyond candidate status until reviewed and approved under this package.
"""


ACCEPTANCE_CRITERIA = """# Canonical Source Acceptance Criteria

A source may be accepted into Corpus C1 only if all required controls are satisfied.

## Required Criteria

| Control | Requirement | Result |
|---|---|---|
| Authority | Source origin is authoritative, primary, or explicitly delegated | REQUIRED |
| Provenance | Source lineage is known and documentable | REQUIRED |
| Custody | Acquisition path is recorded | REQUIRED |
| Integrity | Hash or equivalent fixed reference is recorded where applicable | REQUIRED |
| Rights | Usage permission or internal authorization is documented | REQUIRED |
| Scope Fit | Source belongs within approved C1 corpus scope | REQUIRED |
| Version Clarity | Version, date, or publication state is known | REQUIRED |
| Conflict Review | Known conflicts with existing sources are identified | REQUIRED |
| Privacy Review | Sensitive, regulated, or restricted data is flagged | REQUIRED |
| Revocation Path | Source can be quarantined or removed if challenged | REQUIRED |

## Disqualifying Conditions

A source must be rejected or quarantined if:

- origin is unknown
- authority cannot be established
- custody path is undocumented
- usage rights are unclear
- source contains prohibited data
- source is materially obsolete without historical labeling
- source conflicts with a higher-trust canonical source
- source integrity cannot be reasonably established

## Acceptance Outcomes

Allowed decisions:

- APPROVED_CANONICAL
- APPROVED_REFERENCE_ONLY
- QUARANTINED_PENDING_REVIEW
- REJECTED
- ESCALATED
"""


PROVENANCE_TAXONOMY = """# Provenance Taxonomy

## Trust Tiers

| Tier | Label | Description |
|---|---|---|
| P0 | Primary Authoritative | Original source of truth; official system, owner, policy, legal record, or canonical artifact |
| P1 | Delegated Authoritative | Approved derivative maintained by accountable owner |
| P2 | Verified Reference | Reliable supporting material, not controlling authority |
| P3 | Unverified Candidate | Potentially useful but not yet validated |
| P4 | Conflicted / Deprecated | Known conflict, supersession, or deprecation |
| P5 | Prohibited / Rejected | Not admissible for C1 |

## Provenance Fields

Each candidate source must record:

- source_id
- title
- source_type
- origin_owner
- acquisition_method
- acquired_by
- acquired_at
- custody_path
- version_or_date
- integrity_reference
- rights_basis
- provenance_tier
- review_status
- reviewer
- decision_date
- decision_rationale

## Conflict Rule

When sources conflict:

1. P0 overrides P1-P5
2. Newer approved canonical source overrides older canonical source only if supersession is explicit
3. Policy/legal authority overrides informal guidance
4. Conflicted sources remain quarantined until resolved
"""


CHAIN_OF_CUSTODY = """# Chain-of-Custody Standard

Every candidate source requires a custody record.

## Minimum Custody Record

- Who acquired it
- When it was acquired
- From where it was acquired
- How it was acquired
- Whether it was modified
- Where the original is stored
- Whether an immutable reference exists
- Whether hash/checksum was captured
- Who reviewed it
- What decision was made

## Modification Rule

Candidate sources must not be altered prior to review.

If normalization is later authorized, the normalized copy must preserve a link to the original source and its custody record.

## Hashing Rule

Where technically possible, record:

- SHA256 hash
- file size
- file name
- original URI or storage location
- acquisition timestamp
"""


EVIDENCE_RULES = """# Evidence Admissibility Rules

Evidence is admissible for C1 review only if it is:

1. Relevant to source authority, provenance, rights, integrity, or scope
2. Attributable to a known origin
3. Preserved with sufficient metadata
4. Linked to the candidate source
5. Reviewable by a human approver

## Evidence Types

| Type | Use |
|---|---|
| OWNER_ATTESTATION | Confirms authority or stewardship |
| SYSTEM_EXPORT | Confirms source from authoritative system |
| POLICY_REFERENCE | Confirms governing requirement |
| LEGAL_OR_RIGHTS_RECORD | Confirms permission or restriction |
| HASH_RECORD | Confirms integrity |
| CHANGE_LOG | Confirms version lineage |
| REVIEW_NOTE | Captures human review judgment |
| CONFLICT_RECORD | Documents contradiction or supersession |

## Non-Admissible Evidence

- unattributed screenshots
- unverifiable summaries
- AI-generated claims without source references
- stale references without date context
- undocumented copies
"""


REVIEW_CHECKLIST = """# C1 Manual Review Checklist

For each source candidate:

## Identity

- [ ] Source has unique source_id
- [ ] Title is clear
- [ ] Source type is recorded
- [ ] Origin owner is known
- [ ] Version/date is known

## Provenance

- [ ] Acquisition method is recorded
- [ ] Acquired by is recorded
- [ ] Acquisition timestamp is recorded
- [ ] Custody path is recorded
- [ ] Integrity reference is recorded where applicable

## Authority

- [ ] Source authority is established
- [ ] Owner/steward is identifiable
- [ ] Source is in C1 scope
- [ ] Supersession/conflict status checked

## Risk

- [ ] Privacy sensitivity assessed
- [ ] Rights/usage basis recorded
- [ ] Restricted content flagged
- [ ] Quarantine path available

## Decision

- [ ] Decision recorded
- [ ] Reviewer recorded
- [ ] Decision rationale recorded
- [ ] Conditions or limitations recorded
"""


APPROVAL_MATRIX = """# C1 Approval Matrix

| Decision | Meaning | Allowed Next State |
|---|---|---|
| APPROVED_CANONICAL | Source accepted as canonical for C1 | Eligible for future ingestion only after separate ingestion gate |
| APPROVED_REFERENCE_ONLY | Source may support review but is not canonical | Reference register only |
| QUARANTINED_PENDING_REVIEW | Source requires more evidence or conflict resolution | Quarantine register |
| REJECTED | Source is inadmissible | Rejected register |
| ESCALATED | Higher authority decision required | Escalation queue |

## Minimum Approval Authority

| Source Type | Required Reviewer |
|---|---|
| Policy / governance | Governance owner |
| Legal / contractual | Legal or delegated authority |
| Technical architecture | Technical owner |
| Operational procedure | Process owner |
| Training / knowledge material | Corpus steward |
| Sensitive data source | Privacy/security reviewer |

## Decision Integrity Rule

No source may be marked APPROVED_CANONICAL without:

- reviewer identity
- decision date
- rationale
- provenance tier
- rights basis
- custody path
"""


QUARANTINE = """# Quarantine and Revocation Procedure

## Quarantine Triggers

A source must be quarantined if:

- authority is challenged
- ownership is unclear
- rights are disputed
- integrity is uncertain
- conflict is discovered
- sensitive data is found
- source is superseded
- review evidence is incomplete

## Quarantine Effects

While quarantined:

- source is not canonical
- source is not ingestible
- source is not indexable
- source is not available for enrichment
- source is not available for downstream workflows

## Revocation Record

A revocation must record:

- source_id
- reason
- trigger event
- reviewer
- decision date
- affected dependent artifacts
- remediation instruction
"""


SOURCE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "C1 Source Candidate",
    "type": "object",
    "required": [
        "source_id",
        "title",
        "source_type",
        "origin_owner",
        "acquisition_method",
        "acquired_by",
        "acquired_at",
        "custody_path",
        "rights_basis",
        "provenance_tier",
        "review_status",
    ],
    "properties": {
        "source_id": {"type": "string", "minLength": 3},
        "title": {"type": "string", "minLength": 1},
        "source_type": {
            "type": "string",
            "enum": [
                "policy",
                "procedure",
                "legal",
                "technical",
                "operational",
                "training",
                "reference",
                "system_export",
                "other",
            ],
        },
        "origin_owner": {"type": "string", "minLength": 1},
        "acquisition_method": {"type": "string", "minLength": 1},
        "acquired_by": {"type": "string", "minLength": 1},
        "acquired_at": {"type": "string", "format": "date-time"},
        "custody_path": {"type": "string", "minLength": 1},
        "version_or_date": {"type": "string"},
        "integrity_reference": {"type": "string"},
        "rights_basis": {"type": "string", "minLength": 1},
        "provenance_tier": {
            "type": "string",
            "enum": ["P0", "P1", "P2", "P3", "P4", "P5"],
        },
        "review_status": {
            "type": "string",
            "enum": [
                "NOT_REVIEWED",
                "APPROVED_CANONICAL",
                "APPROVED_REFERENCE_ONLY",
                "QUARANTINED_PENDING_REVIEW",
                "REJECTED",
                "ESCALATED",
            ],
        },
        "reviewer": {"type": "string"},
        "decision_date": {"type": "string"},
        "decision_rationale": {"type": "string"},
        "risk_flags": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "privacy",
                    "security",
                    "legal",
                    "rights_unclear",
                    "conflict",
                    "deprecated",
                    "sensitive",
                    "unknown_origin",
                ],
            },
        },
    },
    "additionalProperties": False,
}


EVIDENCE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "C1 Evidence Record",
    "type": "object",
    "required": [
        "evidence_id",
        "source_id",
        "evidence_type",
        "description",
        "origin",
        "recorded_by",
        "recorded_at",
    ],
    "properties": {
        "evidence_id": {"type": "string", "minLength": 3},
        "source_id": {"type": "string", "minLength": 3},
        "evidence_type": {
            "type": "string",
            "enum": [
                "OWNER_ATTESTATION",
                "SYSTEM_EXPORT",
                "POLICY_REFERENCE",
                "LEGAL_OR_RIGHTS_RECORD",
                "HASH_RECORD",
                "CHANGE_LOG",
                "REVIEW_NOTE",
                "CONFLICT_RECORD",
            ],
        },
        "description": {"type": "string", "minLength": 1},
        "origin": {"type": "string", "minLength": 1},
        "recorded_by": {"type": "string", "minLength": 1},
        "recorded_at": {"type": "string", "format": "date-time"},
        "evidence_location": {"type": "string"},
    },
    "additionalProperties": False,
}


DECISION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "C1 Review Decision",
    "type": "object",
    "required": [
        "decision_id",
        "source_id",
        "decision",
        "reviewer",
        "decision_date",
        "rationale",
    ],
    "properties": {
        "decision_id": {"type": "string", "minLength": 3},
        "source_id": {"type": "string", "minLength": 3},
        "decision": {
            "type": "string",
            "enum": [
                "APPROVED_CANONICAL",
                "APPROVED_REFERENCE_ONLY",
                "QUARANTINED_PENDING_REVIEW",
                "REJECTED",
                "ESCALATED",
            ],
        },
        "reviewer": {"type": "string", "minLength": 1},
        "decision_date": {"type": "string", "format": "date"},
        "rationale": {"type": "string", "minLength": 1},
        "conditions": {"type": "string"},
    },
    "additionalProperties": False,
}


SOURCE_FIELDS = [
    "source_id",
    "title",
    "source_type",
    "origin_owner",
    "acquisition_method",
    "acquired_by",
    "acquired_at",
    "custody_path",
    "version_or_date",
    "integrity_reference",
    "rights_basis",
    "provenance_tier",
    "review_status",
    "reviewer",
    "decision_date",
    "decision_rationale",
    "risk_flags",
]

EVIDENCE_FIELDS = [
    "evidence_id",
    "source_id",
    "evidence_type",
    "description",
    "origin",
    "recorded_by",
    "recorded_at",
    "evidence_location",
]

DECISION_FIELDS = [
    "decision_id",
    "source_id",
    "decision",
    "reviewer",
    "decision_date",
    "rationale",
    "conditions",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()


def build_status_report() -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    return f"""# C1 Readiness Status

Generated: {generated_at}

## Current Status

C1 governance package has been created.

## Boundary Status

| Control | Status |
|---|---|
| No ingestion | PRESERVED |
| No indexing | PRESERVED |
| No semantic enrichment | PRESERVED |
| No automation activation | PRESERVED |
| No downstream intelligence workflows | PRESERVED |

## Required Before Gate Advancement

- Source candidates populated
- Evidence records attached
- Manual review completed
- Decision register completed
- Quarantine/rejection records handled
- Governance owner approval recorded

## Current Readiness

NO-GO for ingestion.

Reason: C1 manual canonical-source acquisition review has not yet produced approved canonical sources.
"""


def main() -> None:
    write_text(ROOT / "00_BOUNDARY.md", BOUNDARY)
    write_text(ROOT / "01_CANONICAL_SOURCE_ACCEPTANCE_CRITERIA.md", ACCEPTANCE_CRITERIA)
    write_text(ROOT / "02_PROVENANCE_TAXONOMY.md", PROVENANCE_TAXONOMY)
    write_text(ROOT / "03_CHAIN_OF_CUSTODY_STANDARD.md", CHAIN_OF_CUSTODY)
    write_text(ROOT / "04_EVIDENCE_ADMISSIBILITY_RULES.md", EVIDENCE_RULES)
    write_text(ROOT / "05_REVIEW_CHECKLIST.md", REVIEW_CHECKLIST)
    write_text(ROOT / "06_APPROVAL_MATRIX.md", APPROVAL_MATRIX)
    write_text(ROOT / "07_QUARANTINE_AND_REVOCATION.md", QUARANTINE)

    write_json(ROOT / "schemas/source_candidate.schema.json", SOURCE_SCHEMA)
    write_json(ROOT / "schemas/evidence_record.schema.json", EVIDENCE_SCHEMA)
    write_json(ROOT / "schemas/review_decision.schema.json", DECISION_SCHEMA)

    write_csv(ROOT / "registers/source_candidates.csv", SOURCE_FIELDS)
    write_csv(ROOT / "registers/evidence_register.csv", EVIDENCE_FIELDS)
    write_csv(ROOT / "registers/decision_register.csv", DECISION_FIELDS)

    write_text(ROOT / "reports/C1_READINESS_STATUS.md", build_status_report())

    print(f"Created C1 governance kit at: {ROOT.resolve()}")
    print("Status: NO-GO for ingestion. Governance review package only.")


if __name__ == "__main__":
    main()
