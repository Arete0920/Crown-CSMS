# CROWN Final 95+ Sprint Index

Status: ACTIVE FINAL-SPRINT INDEX
Authority: Non-shipping index until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Current decision posture

- Sprint execution: ACTIVE.
- Unrestricted production release: NOT APPROVED.
- Current controlling authority: `docs/CURRENT_RELEASE_STATUS.md`.
- Required final target: every production-visible area complete, clean, wired, tested, evidence-backed, and 95+.

## Control artifacts

| Artifact | Purpose |
|---|---|
| `CONTROL_20260530.md` | Establishes final sprint standard, current posture, and work lanes |
| `INTEGRITY_OPERATING_STANDARD_20260530.md` | Integrity, evidence, mission, and source-hygiene operating standard |
| `VSCODE_COMMAND_PACK_20260530.md` | Local evidence command pack that must be run from repo root |
| `VSCODE_SINGLE_BLOCK_EVIDENCE_RUN_20260530.md` | Single copy/paste local evidence runner for VS Code PowerShell |
| `FINAL_95_PLUS_ACCEPTANCE_MATRIX_20260530.md` | Module/function acceptance matrix and 95+ scoring standard |
| `SCORE_GAP_CLOSURE_MAP_20260530.md` | Explicit blocker-to-closure map for every low-score area |
| `PUNCH_LIST_20260530.md` | Prioritized P0/P1/P2/P3 punch list |
| `ROUTE_API_ROLE_DATA_AUDIT_20260530.md` | Connector-backed audit for routes, APIs, roles, data readiness |
| `COMPLIANCE_CUSTOMER_READINESS_AUDIT_20260530.md` | Compliance/customer trust blocker audit |
| `SANDBOX_READY_GATE_20260601.md` | June 1 sandbox-readiness gate and required proof |
| `PRODUCTION_RELEASE_ROADMAP_20260701.md` | July 1 production-readiness roadmap and required proof |
| `FINAL_SIGNOFF_TEMPLATE_20260530.md` | Final signoff template; not a signoff until all TBDs are filled with proof |
| `BACKEND_API_COMPLETION_QUEUE_20260530.md` | Backend/API completion queue and scoring lock |
| `FRONTEND_DASHBOARD_WIZARD_COMPLETION_QUEUE_20260530.md` | Frontend/dashboard/wizard completion queue and production-visibility rules |
| `FIRST_FAILURE_TRIAGE_RUNBOOK_20260530.md` | First-failure triage method after evidence pack execution |
| `MODULE_IMPLEMENTATION_SEQUENCE_20260530.md` | Ordered module completion sequence for 95+ closure |
| `EVIDENCE_REVIEW_PROTOCOL_20260530.md` | Protocol for reading generated evidence and determining next action |

## Required local proof path

Run one of the following from repo root:

- `docs/release/final-95-plus-sprint/VSCODE_COMMAND_PACK_20260530.md`
- `docs/release/final-95-plus-sprint/VSCODE_SINGLE_BLOCK_EVIDENCE_RUN_20260530.md`

Then commit the generated evidence root under:

`audit-artifacts/final-95-plus-sprint/<timestamp>/`

## Operating sequence

1. Pull latest `main`.
2. Run the VS Code evidence pack.
3. Commit generated evidence.
4. Review evidence using `EVIDENCE_REVIEW_PROTOCOL_20260530.md`.
5. Fix the first failure only.
6. Re-run focused proof.
7. Repeat until P0 gates pass.
8. Close route/API/role/data matrices.
9. Close module-by-module 95+ rows.
10. Complete compliance/customer trust artifacts.
11. Run deploy parity and protected-spine proof.
12. Only then update the canonical release authority and final scorecard.

## Target gates

| Target | Gate file | Current sprint status |
|---|---|---|
| Sandbox-ready process by 2026-06-01 | `SANDBOX_READY_GATE_20260601.md` | NO-GO until evidence passes |
| Production marketplace release by 2026-07-01 | `PRODUCTION_RELEASE_ROADMAP_20260701.md` | NO-GO until every release gate is 95+ |

## Forbidden shortcuts

- No production claim from registry presence.
- No production claim from route presence.
- No production claim from dashboard shell presence.
- No production claim from old/stale evidence.
- No unrestricted GO while parity/protected-spine/compliance/customer readiness are incomplete.

## Status language

Allowed:

- `Sprint active; production release not yet approved.`
- `Evidence generated; first failure under review.`
- `Focused fix applied; proof rerun required.`
- `Gate passed on current candidate SHA.`

Forbidden:

- `Done` without evidence.
- `Probably ready`.
- `Good enough`.
- `Will clean later`.
- `Production ready` before all final gates pass.
