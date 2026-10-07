# Workflow Consolidation Plan

Last updated: 2026-10-06

## Goal

Keep GitHub Actions small, authoritative, fail-closed, and understandable for a solo-maintained production repository. Top-level workflows are reserved for required merge gates, deployment/runtime operations, domain verification that materially differs from the general test suite, resilience drills, security, and repository maintenance.

## October 2026 consolidation

- Starting top-level workflow count: **118**
- Canonical active workflow count after this cleanup: **45**
- Reduction: **73 workflows removed (62%)**
- Underlying application tests, audit scripts, and release evidence code remain in the repository unless independently obsolete.
- No branch-required workflow identified in the current required-check map was removed.
- Legacy phase, RC, proof-ceremony, sandbox-depth, duplicate evidence-contract, duplicate dependency-scan, duplicate deploy-dispatch, and duplicate smoke entrypoints were retired.
- `tools/verify_workflow_policy.py` now enforces the canonical workflow filename inventory, so workflow sprawl cannot silently return.

## Canonical workflow classes

### Required merge and repository gates

- `backend-gate.yml`
- `codeql.yml`
- `contract-gate.yml`
- `crown-release-authority-gates.yml`
- `dashboards-build-gate.yml`
- `dependency-audit.yml`
- `dependency-review.yml`
- `pytest-gate.yml`
- `release-verify.yml`
- `repository-policy.yml`
- `schema-governance.yml`
- `secret-scan.yml`
- `tests.yml`

### Core CI and specialized verification

- `ci.yml`
- `accounting-verification.yml`
- `classroom-verification.yml`
- `content-operations-verification.yml`
- `finance-final-hardening.yml`
- `migration-lock-gate.yml`
- `tenant-isolation-gate.yml`
- `ui-proof-gate.yml`
- `wizard-e2e-evidence-gate.yml`
- `pr-preflight.yml`
- `crown-claims-guard.yml`

### Deployment and runtime operations

- `azure-classroom-preflight.yml`
- `azure-drift-watchdog.yml`
- `deploy-dashboard.yml`
- `deploy-dev.yml`
- `deploy-prod.yml`
- `schema-migration-stage.yml`
- `dev-smoke.yml`
- `demo-reset.yml`
- `ops-reset-dev.yml`
- `prod-health-watch.yml`
- `prod-rollback-on-failure.yml`
- `production-certification-evidence.yml`

### Resilience, security, and maintenance

- `isolated-postgres-restore-drill.yml`
- `prod-immutable-rollback-drill.yml`
- `recovery-control-drill.yml`
- `secrets-control-drill.yml`
- `license-audit.yml`
- `sbom-generation.yml`
- `repository-freshness.yml`
- `stale-branches.yml`
- `workflow-permissions-audit.yml`

## Operating rules

1. **Do not create a new top-level workflow for a module, phase, proof packet, or one-time investigation.**
2. Add ordinary tests to an existing canonical workflow or test suite.
3. New deployment or resilience entrypoints require a distinct operational lifecycle that cannot safely live in an existing workflow.
4. Every external Action reference must use a full immutable commit SHA.
5. Every runner job must have a timeout.
6. Every workflow must declare least-privilege permissions and a concurrency policy.
7. Required PR gates fail closed. Runtime certification may report blocked/not-verified, but must not convert an actual gate failure into success.
8. Production deployment remains exact-tag/exact-SHA based; mutable image labels must never be deployment authority.
9. Remove obsolete workflow entrypoints when their purpose is absorbed; do not leave historical workflows active for provenance.
10. Historical evidence belongs in documentation/audit records, not in permanently active Actions entrypoints.

## Next reduction

The remaining 45 workflows are the safe canonical ceiling under the current required-check and operational model. A second reduction should occur only after GitHub branch-protection/ruleset administration is updated so several existing required contexts can be replaced by a smaller set of stable aggregate gates. That administrative change must precede deleting required check-producing workflows.
