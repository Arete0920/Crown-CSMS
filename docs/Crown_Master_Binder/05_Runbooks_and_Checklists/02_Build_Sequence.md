# Build Sequence

> Authority Scope Notice (2026-05-29)
>
> This document is an operational build-sequencing runbook and not a controlling repository-level release authority source.
>
> Current controlling release-authority sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

## Phase 1 - Inventory and Canon Lock
- inventory everything
- classify nothing yet unless obvious
- no deletion
- lock naming and structure rules

## Phase 2 - Classification and Approval
- rewrite and approve canons
- classify keep/rewrite/drop
- approve phase-one scope
- confirm product taxonomy

## Phase 3 - Archive and Purge Readiness
- produce archive packages
- verify archive completeness
- prepare deletion checklist
- confirm restore confidence

## Phase 4 - Controlled Purge and Clean Bootstrap
- controlled purge
- clean bootstrap
- confirm approved structure only
- begin core build

## Phase 5 - Core Build
- auth
- RBAC
- tenant isolation
- audit
- canonical SIS truth
- shared backend contracts
- shared frontend shell

## Phase 6 - First-Wave Modules
- admissions
- re-enrollment
- billing / payments
- communications + portals

## Phase 7 - Hardening, Integration, Release Readiness
- test hardening
- integration validation
- role and tenant proofs
- release evidence
- go/no-go

## Control rule
No movement to the next phase without gate approval.
