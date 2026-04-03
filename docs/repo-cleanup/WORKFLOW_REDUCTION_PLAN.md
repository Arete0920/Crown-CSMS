# Workflow Reduction Plan (Phase 2 Proposal)

This plan is inventory-first and non-destructive. No workflow files are deleted in Phase 1.

## Proposed Canonical Keep Set

- `ci.yml`
- `tests.yml`
- `codeql.yml`
- `dependency-review.yml`
- `secret-scan.yml`
- `deploy-dev.yml`
- `deploy-prod.yml`
- `system-health.yml` (or `prod-health-watch.yml`, keep one canonical health monitor)

## Grouping By Function

### Core CI, Security, and Governance (KEEP)

- `ci.yml`, `tests.yml`, `codeql.yml`, `dependency-review.yml`, `secret-scan.yml`

### Deploy Pipelines (KEEP + REVIEW)

- KEEP: `deploy-dev.yml`, `deploy-prod.yml`
- REVIEW: `deploy-prod-dispatch.yml`, `deploy-dashboard.yml`, `deploy-integrity-proof.yml`, `prod-integrity-proof.yml`

### Health and Smoke (CONSOLIDATE)

- REVIEW/CONSOLIDATE: `dev-smoke.yml`, `dev-smoke-azure-dev.yml`, `prod-health-watch.yml`, `system-health.yml`, `msgraph-smoke.yml`

### Demo and Proof Ceremony (ARCHIVE CANDIDATES)

- ARCHIVE candidates after owner confirmation:
  - `phase3-demo-proof-pack.yml`
  - `phase3-runtime-proof.yml`
  - `phase4-gradebook-demo-proof.yml`
  - `proof-ceremony.yml`
  - `proof-ceremony-prod.yml`
  - `proof-ceremony-after-prod.yml`
  - `proof-gradebook.yml`
  - `demo-contract-freeze.yml`
  - `demo-reset.yml`
  - `demo-reset-smoke.yml`
  - `demo-surface-gate.yml`

### Specialized Gates and Legacy One-Offs (REMOVE_LATER CANDIDATES)

- `backend-gate.yml`
- `contract-gate.yml`
- `routes-gate.yml`
- `migration-lock-gate.yml`
- `lockdown-golden-path-gate.yml`
- `pytest-gate.yml`
- `ui-proof-gate.yml`
- `ui-proof-gates.yml`
- `ui-shell-gate.yml`
- `frontend-shell-certification.yml`
- `backend-shell-seeded-proof.yml`
- `backend-shell-write-and-lifecycle-proof.yml`
- `shell-backend-contract-parity.yml`
- `spine-audit.yml`
- `rc-gate.yml`
- `rc-build-sha-proof.yml`
- `rc-promotion-gate.yml`
- `rc-runbook.yml`
- `rc-tier1-deployed-smoke.yml`
- `phase1-gate.yml`
- `crown-magus0-gate.yml`
- `dashboards-build-gate.yml`

## Duplicate Signals

- UI proof duplication: `ui-proof-gate.yml` vs `ui-proof-gates.yml`
- Proof ceremony duplication: `proof-ceremony.yml`, `proof-ceremony-prod.yml`, `proof-ceremony-after-prod.yml`
- RC ceremony overlap: `rc-*` workflows with overlapping release gate behavior
- Deploy integrity overlap: `deploy-integrity-proof.yml` and `prod-integrity-proof.yml`

## Phase 2 Execution Guardrails

- Confirm branch protection required checks before any removal.
- Convert deprecated flows to manual `workflow_dispatch` before archival.
- Archive candidates to `artifacts/archive/workflows/` only after owner sign-off.
- Remove files only after two consecutive green runs on canonical workflows.
