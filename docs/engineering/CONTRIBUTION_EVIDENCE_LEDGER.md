# Contribution Evidence Ledger

**Status:** Canonical contributor-attribution control  
**Owner:** TC Megahan, Founder/Product Owner  
**Related policy:** `docs/engineering/HUMAN_OWNERSHIP_AND_AI_ASSISTANCE_POLICY.md`  
**Related program:** #1432

## Purpose

This ledger records contributor roles and specific contribution claims only when supported by durable evidence.

It does not replace Git history, pull requests, issues, reviews, signed records, project documents, or other retained evidence. When evidence is incomplete, the status is `NOT VERIFIED`.

## Current role record

| Person | Current role status | Historical contribution status | Attribution rule |
|---|---|---|---|
| TC Megahan | Founder/Product Owner; repository owner; requirements, technical-direction, acceptance, and release authority | Product ownership and repository authority established | Attribute specific implementation, testing, review, design, or documentation work only where durable evidence supports it |
| Anthony Rizzo | Founding/early collaborator | Specific work `NOT VERIFIED` in this ledger | Credit modules, files, architecture, implementation, testing, review, documentation, or operations only with supporting evidence |
| Ayush Agarwal | Founding/early collaborator | Specific work `NOT VERIFIED` in this ledger | Credit modules, files, architecture, implementation, testing, review, documentation, or operations only with supporting evidence |
| Jed Hansen | Founding/early collaborator | Specific work `NOT VERIFIED` in this ledger | Credit modules, files, architecture, implementation, testing, review, documentation, or operations only with supporting evidence |
| Johnny Megahan | New collaborator | No historical contribution recorded | Do not assign prior work; add future contributions when evidence exists |
| Evan Lesage | New collaborator | No historical contribution recorded | Do not assign prior work; add future contributions when evidence exists |

## Evidence-entry format

Add one row for each defensible contribution claim.

| Person | Contribution type | Scope | Evidence | Date or range | Verification status | Notes |
|---|---|---|---|---|---|---|
| _Example_ | Implementation | `backend/example/` | PR #0000 and commit SHA | YYYY-MM-DD | VERIFIED | Human identity and scope confirmed |

Allowed contribution types include:

- Product ownership
- Requirements
- Architecture or design
- Implementation
- Testing
- Review
- Documentation
- Operations or release support

## Verification statuses

- `VERIFIED` — direct durable evidence supports the claim.
- `PARTIALLY VERIFIED` — evidence supports part of the claim; record the exact boundary.
- `NOT VERIFIED` — evidence has not been found or is insufficient.
- `DISPUTED` — sources conflict; do not use externally until resolved.
- `SUPERSEDED` — a newer evidence record replaces the claim.

## Evidence review procedure

1. Begin with a specific claim, not a desired attribution.
2. Search commits, pull requests, reviews, issues, project documents, signed records, and retained external evidence.
3. Confirm that the identity in the evidence maps to the named person.
4. Record exact paths, PR numbers, commit SHAs, dates, or document references.
5. Separate requirements, design, implementation, testing, review, documentation, and release support.
6. Record uncertainty explicitly.
7. Do not alter historical commit authorship merely to improve presentation.
8. Reconcile conflicting evidence before external use.

## AI-assisted work

AI assistance may be disclosed in a supporting pull request or evidence record, but it does not replace the human owner or evidence-backed contributors.

A commit created through an IDE assistant, connector, chat tool, or automation does not by itself establish who designed, implemented, reviewed, tested, or accepted the work. Those roles require separate evidence.

## External-use rule

Client-, buyer-, diligence-, and future-owner-facing materials must use this ledger and its underlying evidence. They must not:

- assign specific historical work to Anthony Rizzo, Ayush Agarwal, or Jed Hansen without evidence;
- assign historical work to Johnny Megahan or Evan Lesage;
- imply that AI tools owned requirements, architecture, approval, or release decisions;
- convert `NOT VERIFIED` claims into definitive statements;
- describe repository submission metadata as complete proof of authorship.