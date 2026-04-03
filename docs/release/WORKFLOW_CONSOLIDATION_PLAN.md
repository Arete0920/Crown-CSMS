# Workflow Consolidation Plan

Last updated: 2026-04-02

## Goal

Reduce the current GitHub Actions workflow sprawl to a canonical set of 12 workflows that
cover security, test gates, deployments, smoke checks, demo reset, and release verification.

## Current State Snapshot

- Phase 2 workflow classification completed and documented in:
	- `docs/repo-cleanup/WORKFLOW_CLASSIFICATION_PHASE2.md`
	- `docs/repo-cleanup/WORKFLOW_TRIGGER_MAP_PHASE2.md`
	- `docs/repo-cleanup/REQUIRED_CHECKS_MAP_PHASE2.md`
- Two low-value workflows were removed in Phase 2:
	- `.github/workflows/msgraph-smoke.yml`
	- `.github/workflows/demo-surface-gate.yml`
- Remaining consolidation, required-check hardening, and noise reduction are tracked as follow-up actions.

## Canonical Target Set

| Workflow | Purpose |
|---|---|
| codeql.yml | Static security analysis |
| dependency-audit.yml | pip-audit and npm audit |
| backend-gate.yml | Django tests and API contracts |
| frontend-gate.yml | Frontend tests and smoke |
| contract-gate.yml | API contract validation |
| secret-scan.yml | Secret detection |
| deploy-prod.yml | Production deployment |
| deploy-dev.yml | Development deployment |
| dev-smoke.yml | Post-deploy development smoke |
| prod-health-watch.yml | Production health polling |
| demo-reset.yml | Manual demo reset and seed |
| release-verify.yml | Manual pre-release verification |

## Known Duplicate / Legacy Candidates

- ui-proof-gates.yml -> ui-proof-gate.yml
- dev-smoke-azure-dev.yml -> dev-smoke.yml
- deploy-prod-dispatch.yml -> deploy-prod.yml
- demo-reset-smoke.yml -> demo-reset.yml
- tests.yml -> ci.yml
- dependency-scan.yml -> dependency-audit.yml

## Execution Notes

1. Verify recent run history before deleting a workflow.
2. Keep a single canonical workflow for each operational purpose.
3. Update branch protection required checks only after canonical workflows are green on `main`.
4. Preserve evidence of the before and after workflow inventory for the release packet.

## Governance Caveat

Current ruleset snapshot shows only one required check context (`proof-ceremony`).
Additional checks should be promoted to required only after they are stable and green on main.
See `docs/release/BRANCH_PROTECTION_EVIDENCE.md` and `docs/release/FINAL_RELEASE_GATE.md`.