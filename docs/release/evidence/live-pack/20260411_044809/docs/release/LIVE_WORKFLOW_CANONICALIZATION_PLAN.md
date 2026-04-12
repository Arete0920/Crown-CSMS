# LIVE WORKFLOW CANONICALIZATION PLAN

Generated UTC: 2026-04-11T08:47:22.3506305Z

## Summary
- workflow count: 53
- duplicate cluster count: 4
- archive candidate count: 48
- archived count: 0

## Review Matrix
- azure-drift-watchdog.yml | group=deploy | action=KEEP_PRIMARY_REVIEW
- crown-magus0-gate.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- dashboards-build-gate.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- demo-reset.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- deploy-dashboard.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- deploy-dev.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- deploy-integrity-proof.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- deploy-prod.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- deploy-prod-dispatch.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- dev-smoke.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- dev-smoke-azure-dev.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- ops-reset-dev.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- prod-health-watch.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- prod-integrity-proof.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- proof-ceremony-after-prod.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- proof-ceremony-prod.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- rc-build-sha-proof.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- rc-gate.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- rc-promotion-gate.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- rc-tier1-deployed-smoke.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- spine-audit.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- system-health.yml | group=deploy | action=REVIEW_DUPLICATE_CLUSTER
- backend-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- backend-shell-seeded-proof.yml | group=proof_gate | action=KEEP_PRIMARY_REVIEW
- backend-shell-write-and-lifecycle-proof.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- ci.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- ci-meta-gate-authoring.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- contract-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- demo-reset-smoke.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- frontend-shell-certification.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- gradebookro-ui-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- lockdown-golden-path-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- migration-lock-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- phase1-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- phase3-demo-proof-pack.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- phase3-runtime-proof.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- phase4-gradebook-demo-proof.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- proof-ceremony.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- proof-gradebook.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- pytest-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- rc-runbook.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- routes-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- secret-scan.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- ui-proof-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- ui-proof-gates.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- ui-shell-gate.yml | group=proof_gate | action=REVIEW_DUPLICATE_CLUSTER
- demo-contract-freeze.yml | group=release | action=KEEP_UNIQUE
- dependency-audit.yml | group=security | action=KEEP_PRIMARY_REVIEW
- dependency-review.yml | group=security | action=REVIEW_DUPLICATE_CLUSTER
- dependency-scan.yml | group=security | action=REVIEW_DUPLICATE_CLUSTER
- shell-backend-contract-parity.yml | group=ui | action=KEEP_PRIMARY_REVIEW
- stale-branches.yml | group=ui | action=REVIEW_DUPLICATE_CLUSTER
- tests.yml | group=ui | action=REVIEW_DUPLICATE_CLUSTER

## Archive Script
- scripts/release/generated/phase13_archive_extra_workflows.ps1
