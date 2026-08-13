# CROWN Post-Completion Improvement Backlog

## Purpose

Preserve high-value architectural and operational improvements discovered during final gap closure without interrupting the current P0 completion program.

This file is a **parking lot, not an active remediation queue**. Items remain deferred until the current gap-closure program, exact successor certification, and owner-handoff priorities are completed unless new evidence proves an item is required to close a current P0 gate or protect security, tenant isolation, data integrity, or release integrity.

## Status values

- `PARKED`
- `PROMOTE TO P0`
- `COMPLETED`
- `REJECTED`

## General improvement backlog

| # | Improvement | Why it matters | Status |
|---|---|---|---|
| 1 | Machine-readable Domain Ownership Registry | Enforces one authoritative write owner per durable domain and reduces rediscovery/duplication. | PARKED |
| 2 | Architecture conformance tests | Adds CI checks for ownership, duplicate writers, tenant authority, protected mutations, and prohibited compatibility writes. | PARKED |
| 3 | Formal Compatibility Registry | Records canonical owner, reason, consumers, write/read status, migration path, and retirement criteria for legacy/bridge models. | PARKED |
| 4 | Universal domain-permission enforcement | Prevents mutating workflows from relying only on authentication; requires explicit business-domain permissions. | PARKED |
| 5 | Destructive/bulk mutation safety standard | Standardizes validate-before-write, persisted collision checks, transactions, idempotency, audit, counts, and rollback/forward-fix behavior. | PARKED |
| 6 | Compliance audit vs. operational telemetry separation | Makes fail-closed security/business audit distinct from best-effort request telemetry. | PARKED |
| 7 | Machine-readable release/authority manifest | Eliminates stale manually maintained current-SHA claims and separates repository, release, deployment, buyer, and turnover status. | PARKED |
| 8 | Permanent full-functional sandbox certification standard | Keeps sandbox proof focused on real business processes and false-positive-resistant assertions, not dashboard tours. | PARKED |
| 9 | Automated stale/superseded branch detection | Reduces repository noise and identifies branches with unique work before cleanup. | PARKED |
| 10 | Canonical authority/document generation checks | Prevents duplicate active authorities and stale predecessor/current-successor claims. | PARKED |

## Scheduling-specific improvements discovered during P0 reconciliation

These are **future enhancements unless they become necessary to close the verified Scheduling P0 gap**.

| # | Scheduling improvement | Why it matters | Status |
|---|---|---|---|
| S1 | Scheduling conflict-explanation engine | Return structured teacher/room/student conflict reasons, conflicting section IDs, and time/block context rather than only generic collision text. | PARKED |
| S2 | Dry-run / schedule-plan preview | Allow a complete validation and impact preview before any schedule mutation is committed. | PARKED |
| S3 | Explicit replace-vs-merge commit modes | Prevent omission from silently implying deletion; make destructive replacement an explicit user/API choice. | PARKED |
| S4 | Schedule change-set audit record | Persist before/after counts, created/updated/retired sections, actor, tenant, and reason for each committed schedule plan. | PARKED |
| S5 | Optimistic concurrency/version guard for scheduling sessions | Prevent a stale wizard session from overwriting scheduling changes made after the session was prepared. | PARKED |
| S6 | Capacity and student-conflict validation | Extend canonical scheduling checks beyond teacher/room collisions to section capacity and student timetable conflicts when rostering data is available. | PARKED |
| S7 | Scheduling rollback/restore command | Provide a governed way to reverse a committed schedule change-set using recorded change data. | PARKED |
| S8 | Canonical scheduling performance index review | Revisit indexes/constraints after convergence so persisted collision checks remain efficient at production school scale. | PARKED |

## Promotion rule

An item may leave `PARKED` status before final completion only when current verification proves that it:

1. blocks a P0 gate;
2. is required to fix a verified defect already in the active workstream;
3. is necessary to preserve security, tenant isolation, data integrity, or release integrity; or
4. must be implemented for current certification to remain truthful.

Otherwise it remains parked.

## Active priority at creation

Do not divert from the current P0 gap-closure queue.

1. Finish verified Scheduling canonicalization/remediation.
2. Re-verify Scheduling consumers, migrations, permissions, collision handling, data preservation, frontend/API behavior, and tests.
3. Continue Gate 2 domain-by-domain verification using `FIND -> VERIFY -> CLASSIFY -> FIX DELTA ONLY -> RE-VERIFY -> DISPOSITION -> LOOP`.
4. Preserve already-completed domains unless new evidence proves regression.
5. Complete exact successor release/runtime certification.
6. Complete owner/buyer turnover evidence.
7. Return to this backlog after the P0 program is complete.

## New-entry template

**Date:**  
**Recommendation:**  
**Evidence/source:**  
**Why it matters:**  
**P0 impact:** None / Yes (explain)  
**Recommended future implementation:**  
**Status:** PARKED
