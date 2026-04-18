# Phase 3 Workflow and Branch Rationalization

Generated UTC: 2026-04-11T08:50:51.6232089Z

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
- Remote branch count: 306
- Local branch count: 9
- Open pull request count: 0

## Remote Branch Delete Candidates
- git push origin --delete automerge-workflow
- git push origin --delete chore/canon-tagging-rule
- git push origin --delete ci/proof-add-academics-gradebook-seeds
- git push origin --delete ci/proof-add-seed-demo-school
- git push origin --delete ci/proof-demo-credentials
- git push origin --delete ci/proof-demo-password
- git push origin --delete ci/proof-gradebook-workflow
- git push origin --delete ci/proof-guardrails-canon
- git push origin --delete ci/proof-password-env-var-match
- git push origin --delete ci/proof-pr-trigger
- git push origin --delete ci/proof-seed-fix
- git push origin --delete ci/proof-token-capture-fix
- git push origin --delete cleanup/remove-temp-diagnostic-endpoints
- git push origin --delete commenting-on-pr-issues
- git push origin --delete copilot/check-new-reviewer-comment-activity
- git push origin --delete copilot/gate2b-journal-reversals
- git push origin --delete docs/branch-protection-and-playbook
- git push origin --delete docs/branch-protection-procedures
- git push origin --delete docs/gradebook-proof-milestone
- git push origin --delete docs/proof-bundle-20260209
- git push origin --delete docs/tenant-isolation-canon
- git push origin --delete feat/phase4-visual-polish-nav-home
- git push origin --delete feat/section-assign-wizard
- git push origin --delete feat/wizard-guardrails
- git push origin --delete feature/academics-attendance-grades-readonly
- git push origin --delete feature/admissions-links-readonly
- git push origin --delete feature/billing-household-summary-readonly
- git push origin --delete feature/comms-threads-readonly
- git push origin --delete feature/households-readonly
- git push origin --delete feature/households-scope
- git push origin --delete feature/identity-person-link
- git push origin --delete feature/scheduling-sections-readonly
- git push origin --delete feature/student-core-readonly
- git push origin --delete fix/api-proof-token-storage
- git push origin --delete fix/ci-billing-role
- git push origin --delete fix/ci-smoke-fa-drilldown-validation
- git push origin --delete fix/ci-smoke-fa-json-parse
- git push origin --delete fix/ci-smoke-fa-school-header
- git push origin --delete fix/db-database-url
- git push origin --delete fix/dev-smoke-final-align
- git push origin --delete fix/dev-smoke-stop-requiring-gp-username
- git push origin --delete fix/director-role-permission-check
- git push origin --delete fix/fa-auth-visible-proof
- git push origin --delete fix/golden-path-syntax
- git push origin --delete fix/gp-auth-header-tok
- git push origin --delete fix/gp-remote-seedcontext-ciuser
- git push origin --delete fix/p0-4-smoke-auth-drift-ensure-token
- git push origin --delete fix/router-simple-router
- git push origin --delete fix/smoke-auto-ensure-ci-user
- git push origin --delete ops/build-sha-health-001
- git push origin --delete ops/p0-3-deploy-determinism
- git push origin --delete ops/p0-4-ansi-regex-fix
- git push origin --delete ops/p0-4-smoke-proof
- git push origin --delete ops/p0-4-smoke-proof-ansi-fix
- git push origin --delete ops/p0-4-smoke-proof-final
- git push origin --delete ops/p0-4-smoke-proof-fix
- git push origin --delete ops/p0-4-smoke-proof-fix2
- git push origin --delete ops/p0-4-smoke-proof-fix3
- git push origin --delete pr/academics-spine-ro-contract
- git push origin --delete pr/chore-ignore-gitleaks-artifacts
- git push origin --delete proof/api-gradebook-automated
- git push origin --delete stabilize/durability-lock
- git push origin --delete stabilize/prod-green
- git push origin --delete test/proof-dynamic-section-query
- git push origin --delete test/proof-fix-section-id-field
- git push origin --delete test/proof-ui-dynamic-section

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
