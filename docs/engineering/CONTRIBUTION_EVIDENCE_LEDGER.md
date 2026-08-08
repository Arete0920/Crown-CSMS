# Contribution Evidence Ledger

**Status:** Canonical contributor-attribution control  
**Owner:** TC Megahan, Founder/Product Owner  
**Related policy:** `docs/engineering/HUMAN_OWNERSHIP_AND_AI_ASSISTANCE_POLICY.md`  
**Related program:** #1432

## Purpose

This ledger records creator authority and specific contribution claims only when supported by durable evidence or an explicit Founder/Product Owner attestation recorded as such.

It does not replace Git history, pull requests, issues, reviews, signed records, project documents, or other retained evidence. When evidence is incomplete, the status is `NOT VERIFIED`.

## Current authority record

| Person | Current role status | Historical contribution status | Attribution rule |
|---|---|---|---|
| TC Megahan | Creator of CROWN; Founder/Product Owner; principal product designer; architecture and workflow authority; repository owner; requirements, technical-direction, acceptance, and release authority | Creator, design, architecture, workflow, product ownership, repository authority, and implementation responsibility established by Founder/Product Owner attestation and retained project record | Do not imply TC personally authored every line; use repository evidence when making precise file-, module-, review-, testing-, or documentation-level claims |
| Anthony Rizzo | Founding/early collaborator | Early involvement established by Founder/Product Owner record; specific work not assigned by this ledger without durable evidence | Specific implementation, design, review, testing, documentation, or other credit requires a separate evidence entry |
| Ayush Agarwal | Founding/early collaborator | Early involvement established by Founder/Product Owner record; specific work not assigned by this ledger without durable evidence | Specific implementation, design, review, testing, documentation, or other credit requires a separate evidence entry |
| Jed Hansen | Founding/early collaborator | Early involvement established by Founder/Product Owner record; specific work not assigned by this ledger without durable evidence | Specific implementation, design, review, testing, documentation, or other credit requires a separate evidence entry |
| Johnny Megahan | New/advisory collaborator; prospective reviewer | No historical contribution or completed review disposition recorded | Add contribution or review credit only from the date and durable evidence of that work |
| Evan Lesage | New/advisory collaborator; prospective reviewer | No historical contribution or completed review disposition recorded | Add contribution or review credit only from the date and durable evidence of that work |

## Founder/Product Owner attestation

TC Megahan states that he created CROWN, designed the platform architecture, created the operating and application workflow, directed the implementation, and performed implementation work. Numerous interim coding assistants, collaborators, and development tools supported portions of implementation and related engineering work. They are not individually treated as product owners, architects, founders, acceptance authorities, or release authorities unless separate evidence and authorization establishes such a role.

This attestation establishes creator, architecture, workflow, and product-accountability authority. It does not replace repository evidence for precise claims about who authored, reviewed, tested, or documented a particular file or change.

## Evidence-entry format

Add one row for each defensible contribution claim when a named record is required and authorized.

| Person or authorized identifier | Contribution type | Scope | Evidence | Date or range | Verification status | Notes |
|---|---|---|---|---|---|---|
| _Example_ | Implementation | `backend/example/` | PR #0000 and commit SHA | YYYY-MM-DD | VERIFIED | Identity and scope confirmed |

Allowed contribution types include:

- Product creation and ownership
- Requirements
- Architecture or design
- Workflow design
- Implementation
- Testing
- Review
- Documentation
- Operations or release support

## Verification statuses

- `VERIFIED` — direct durable evidence supports the claim.
- `FOUNDER ATTESTED` — the Founder/Product Owner has explicitly attested to the role or contribution; use the attestation boundary stated in the record.
- `PARTIALLY VERIFIED` — evidence supports part of the claim; record the exact boundary.
- `NOT VERIFIED` — evidence has not been found or is insufficient.
- `DISPUTED` — sources conflict; do not use externally until resolved.
- `SUPERSEDED` — a newer evidence record replaces the claim.

## Evidence review procedure

1. Begin with a specific claim, not a desired attribution.
2. Search commits, pull requests, reviews, issues, project documents, signed records, and retained external evidence.
3. Confirm that the identity in the evidence maps to the named person when identification is necessary.
4. Record exact paths, PR numbers, commit SHAs, dates, document references, or the applicable Founder/Product Owner attestation.
5. Separate creation, requirements, design, architecture, workflow, implementation, testing, review, documentation, and release support.
6. Record uncertainty explicitly.
7. Do not alter historical commit authorship merely to improve presentation.
8. Reconcile conflicting evidence before external use.

## Development-assisted work

Development assistance may be disclosed in a supporting pull request or evidence record, but it does not replace the human owner or evidence-backed contributors.

A commit created through an IDE assistant, connector, coding assistant, chat tool, or automation does not by itself establish who designed, implemented, reviewed, tested, or accepted the work. Those roles require separate evidence or an explicit attestation with a clearly stated boundary.

## External-use rule

Client-, buyer-, diligence-, and future-owner-facing materials must use this ledger and its underlying evidence. They must not:

- assign specific historical work without evidence;
- imply that development assistants owned requirements, architecture, approval, or release decisions;
- convert `NOT VERIFIED` claims into definitive statements;
- describe repository submission metadata as complete proof of authorship;
- imply that TC Megahan personally authored every line of code;
- convert founding/early involvement or new/advisory collaboration into unsupported specific contribution claims.
