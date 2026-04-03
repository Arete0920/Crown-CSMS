# Workflow Inventory Phase 1

Generated on 2026-04-02 for branch chore/github-cleanup-phase1.

| workflow file | classification | rationale | risk level |
|---|---|---|---|
| azure-drift-watchdog.yml | REVIEW_REQUIRED | Needs functional validation against branch protection and release process. | medium |
| backend-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| backend-shell-seeded-proof.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| backend-shell-write-and-lifecycle-proof.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| ci-meta-gate-authoring.yml | REVIEW_REQUIRED | Needs functional validation against branch protection and release process. | medium |
| ci.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| codeql.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| contract-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| crown-magus0-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| dashboards-build-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| demo-contract-freeze.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| demo-reset-smoke.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| demo-reset.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| demo-surface-gate.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| dependency-audit.yml | REVIEW_REQUIRED | Potentially active health/dependency protection path; keep until confirmed. | medium |
| dependency-review.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| dependency-scan.yml | REVIEW_REQUIRED | Potentially active health/dependency protection path; keep until confirmed. | medium |
| deploy-dashboard.yml | REVIEW_REQUIRED | Needs functional validation against branch protection and release process. | medium |
| deploy-dev.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| deploy-integrity-proof.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| deploy-prod-dispatch.yml | REVIEW_REQUIRED | Needs functional validation against branch protection and release process. | medium |
| deploy-prod.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| dev-smoke-azure-dev.yml | REVIEW_REQUIRED | Potentially active health/dependency protection path; keep until confirmed. | medium |
| dev-smoke.yml | REVIEW_REQUIRED | Potentially active health/dependency protection path; keep until confirmed. | medium |
| frontend-shell-certification.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| gradebookro-ui-gate.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| lockdown-golden-path-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| migration-lock-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| msgraph-smoke.yml | REVIEW_REQUIRED | Needs functional validation against branch protection and release process. | medium |
| ops-reset-dev.yml | REVIEW_REQUIRED | Needs functional validation against branch protection and release process. | medium |
| phase1-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| phase3-demo-proof-pack.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| phase3-runtime-proof.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| phase4-gradebook-demo-proof.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| prod-health-watch.yml | REVIEW_REQUIRED | Potentially active health/dependency protection path; keep until confirmed. | medium |
| prod-integrity-proof.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| proof-ceremony-after-prod.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| proof-ceremony-prod.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| proof-ceremony.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| proof-gradebook.yml | DEMO_ONLY | Appears demo/proof specific by naming and scope. | medium |
| pytest-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| rc-build-sha-proof.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| rc-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| rc-promotion-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| rc-runbook.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| rc-tier1-deployed-smoke.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| routes-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| secret-scan.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| shell-backend-contract-parity.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| spine-audit.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
| system-health.yml | REVIEW_REQUIRED | Potentially active health/dependency protection path; keep until confirmed. | medium |
| tests.yml | KEEP_CANONICAL | Core governance/security/deploy/test workflow. | low |
| ui-proof-gate.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| ui-proof-gates.yml | POSSIBLE_DUPLICATE | Naming indicates overlapping proof/ceremony gate scope. | medium |
| ui-shell-gate.yml | LEGACY_OR_ONE_OFF | Specialized gate/proof workflow likely one-off or legacy; verify before consolidation. | high |
