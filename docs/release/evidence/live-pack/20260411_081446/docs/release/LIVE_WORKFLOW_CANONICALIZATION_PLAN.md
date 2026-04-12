# LIVE WORKFLOW CANONICALIZATION PLAN

Generated UTC: 2026-04-11T12:14:46.0373603Z

## Summary
- workflow count: 53
- duplicate cluster count: 4
- archive candidate count: 0
- archived count: 0

## Review Matrix
- azure-drift-watchdog.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- crown-magus0-gate.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- dashboards-build-gate.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- demo-reset.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- deploy-dashboard.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- deploy-dev.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- deploy-integrity-proof.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- deploy-prod.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- deploy-prod-dispatch.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- dev-smoke.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- dev-smoke-azure-dev.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- ops-reset-dev.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- prod-health-watch.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- prod-integrity-proof.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- proof-ceremony-after-prod.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- proof-ceremony-prod.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- rc-build-sha-proof.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- rc-gate.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- rc-promotion-gate.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- rc-tier1-deployed-smoke.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- spine-audit.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- system-health.yml | group=deploy | action=KEEP_REVIEWED_UNIQUE
- backend-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- backend-shell-seeded-proof.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- backend-shell-write-and-lifecycle-proof.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- ci.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- ci-meta-gate-authoring.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- contract-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- demo-reset-smoke.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- frontend-shell-certification.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- gradebookro-ui-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- lockdown-golden-path-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- migration-lock-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- phase1-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- phase3-demo-proof-pack.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- phase3-runtime-proof.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- phase4-gradebook-demo-proof.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- proof-ceremony.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- proof-gradebook.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- pytest-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- rc-runbook.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- routes-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- secret-scan.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- ui-proof-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- ui-proof-gates.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- ui-shell-gate.yml | group=proof_gate | action=KEEP_REVIEWED_UNIQUE
- demo-contract-freeze.yml | group=release | action=KEEP_UNIQUE
- dependency-audit.yml | group=security | action=KEEP_REVIEWED_UNIQUE
- dependency-review.yml | group=security | action=KEEP_REVIEWED_UNIQUE
- dependency-scan.yml | group=security | action=KEEP_REVIEWED_UNIQUE
- shell-backend-contract-parity.yml | group=ui | action=KEEP_REVIEWED_UNIQUE
- stale-branches.yml | group=ui | action=KEEP_REVIEWED_UNIQUE
- tests.yml | group=ui | action=KEEP_REVIEWED_UNIQUE

## Archive Script
- scripts/release/generated/phase13_archive_extra_workflows.ps1
