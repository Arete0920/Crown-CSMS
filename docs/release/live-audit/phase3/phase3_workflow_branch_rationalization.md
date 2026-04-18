# Phase 3 Workflow and Branch Rationalization

Generated UTC: 2026-04-11T11:56:54.1859557Z

## Default Branch
- main

## Workflow Inventory
- Workflow count: 53
- Workflow group count: 5

## Workflow Consolidation Groups
- deploy | workflow_count=22 | workflow_names=azure-drift-watchdog.yml, crown-magus0-gate.yml, dashboards-build-gate.yml, demo-reset.yml, deploy-dashboard.yml, deploy-dev.yml, deploy-integrity-proof.yml, deploy-prod.yml, deploy-prod-dispatch.yml, dev-smoke.yml, dev-smoke-azure-dev.yml, ops-reset-dev.yml, prod-health-watch.yml, prod-integrity-proof.yml, proof-ceremony-after-prod.yml, proof-ceremony-prod.yml, rc-build-sha-proof.yml, rc-gate.yml, rc-promotion-gate.yml, rc-tier1-deployed-smoke.yml, spine-audit.yml, system-health.yml
- proof_gate | workflow_count=24 | workflow_names=backend-gate.yml, backend-shell-seeded-proof.yml, backend-shell-write-and-lifecycle-proof.yml, ci.yml, ci-meta-gate-authoring.yml, contract-gate.yml, demo-reset-smoke.yml, frontend-shell-certification.yml, gradebookro-ui-gate.yml, lockdown-golden-path-gate.yml, migration-lock-gate.yml, phase1-gate.yml, phase3-demo-proof-pack.yml, phase3-runtime-proof.yml, phase4-gradebook-demo-proof.yml, proof-ceremony.yml, proof-gradebook.yml, pytest-gate.yml, rc-runbook.yml, routes-gate.yml, secret-scan.yml, ui-proof-gate.yml, ui-proof-gates.yml, ui-shell-gate.yml
- release | workflow_count=1 | workflow_names=demo-contract-freeze.yml
- security | workflow_count=3 | workflow_names=dependency-audit.yml, dependency-review.yml, dependency-scan.yml
- ui | workflow_count=3 | workflow_names=shell-backend-contract-parity.yml, stale-branches.yml, tests.yml

## Branch Inventory
- Remote branch count: 240
- Local branch count: 9
- Open pull request count: 0

## Remote Branch Delete Candidates
- none

## Local Branch Delete Candidates
- none

## Generated Artifacts
- phase3_workflow_branch_rationalization.json
- phase3_workflow_inventory_enriched.csv
- phase3_workflow_consolidation_groups.csv
- phase3_remote_branch_inventory.csv
- phase3_branch_cleanup_candidates.csv
- phase3_local_branch_inventory.csv
- phase3_remote_branch_delete_commands.txt
- phase3_local_branch_delete_commands.txt
