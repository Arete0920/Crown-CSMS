# CROWN Active Work Queue — 2026-05-29

## Decision

**Release status: NO-GO.**

This queue records the current open PR/issue/CI priorities after the release-authority architecture pass. It is intended to prevent scattered work, premature merges, or false completion claims.

## Current open PRs

| Priority | PR | Title | Current disposition | Required next step |
|---:|---:|---|---|---|
| 1 | #866 | Add full-completion truth gate and blocker tracking | Keep open/draft until release-authority artifacts and blockers are inspectable | Inspect latest `CROWN Release Authority Gates` artifact after workflow diagnostic hardening; remediate failures in order |
| 2 | #861 | Production readiness blocker remediation runner | Keep open until runner is executed and generated proof/code outputs are committed | Run `scripts\execution\verify_production_readiness_remediation.ps1`; commit generated changes only if green |
| 3 | #862 | Spiritual Life formation migration closure runner | Keep open until migration closure runner is executed and generated migration/proof outputs are committed | Run `scripts\execution\verify_spiritual_life_formation_closure.ps1`; commit generated migration/proof artifacts only if green |
| 4 | #860 | Restore Little Lambs proof gates via API alias/auth model/migrations | Keep draft until proof rows are filled and CI failures are resolved | Re-run required check/test/proof gates; do not merge while proof fields are blank |
| 5 | #859 | CROWN scheduling core | Keep draft; backend slice is not complete product scheduling | Rebase/update from main, run backend validation, then complete required scheduling UI/wizard/runtime workflows |

## Current open issues

| Priority | Issue | Title | Why it blocks release | Required next step |
|---:|---:|---|---|---|
| 1 | #863 | Replace dashboard preview/template metrics with live data services | Blocks full-completion and dashboard truth certification | Replace preview/base/template data with live API/service-backed metrics and provenance; run dashboard provenance gate |
| 2 | #864 | Prove all registered wizards complete end-to-end | Blocks wizard and setup workflow certification | Produce per-wizard URL/step/validation/persistence/permission/error/test evidence for all 29 registered wizards |
| 3 | #865 | Backend/runtime proof for later-tier modules | Blocks all-module completion | Add backend/API/service/runtime/permission/render evidence for later-tier modules |
| 4 | #858 | Little Lambs full build | Blocks Little Lambs completion and Crown integration claim | Complete dashboards, wizards, reporting, finance, compliance, enrollment/waitlist, and integration workflows with proof |

## Current CI/proof failures to work down

Observed failing checks on the inspected PR/commit family include:

- `CROWN Release Authority Gates`
- `Spine Audit (Canon Guard)`
- `backend-gate`
- `pytest-gate`
- `Release Verify`
- `Phase3 Runtime Proof Ceremony`
- `Schema Governance`
- `CI - Tests and Checks`
- `Proof Ceremony`
- `Accounting Verification`

Observed successful security/dependency-oriented checks include:

- `secret-scan`
- `Dependency Scan`
- `Dependency Audit`
- `Dependency Review`

## Work order

1. Stabilize PR #866 diagnostics and inspect the release-authority artifact.
2. Fix #863 dashboard live-data/provenance blockers.
3. Fix backend/schema/test failures: `backend-gate`, `pytest-gate`, `Schema Governance`, `CI - Tests and Checks`.
4. Use #861 and #862 runners to generate real migration/remediation proof artifacts.
5. Resolve #864 wizard proof with per-wizard evidence.
6. Resolve #865 later-tier backend/runtime proof.
7. Return to #860 Little Lambs and #859 Scheduling only after the core proof spine is green.

## Merge rule

Do not merge a PR if any of the following are true:

- It is draft and still contains proof placeholders.
- Runtime proof is explicitly not claimed.
- Required local validation has not been run.
- It depends on generated migrations/proof artifacts that have not been committed.
- Release-authority status remains `NO-GO` for the scope being claimed.

## Closure rule

Do not close #863, #864, #865, or #858 until their definition of done has current evidence attached to the reviewed commit.
