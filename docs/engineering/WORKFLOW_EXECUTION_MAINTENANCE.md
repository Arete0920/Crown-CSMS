# Workflow Execution Maintenance

Base: `b0a537fc6ce3bcb26eb6b007b43088bd3da1e2e1`

Branch: `ci/scoped-execution-maintenance`

Outcome: Align workflow ownership and toolchain, cancel superseded PR runs, enable dependency maintenance, and retire obsolete one-time workflows.

Allowed files:

- `.github/CODEOWNERS`
- `.github/ISSUE_TEMPLATE/repository-health-review.yml`
- `.github/dependabot.yml`
- `.github/workflows/apply-ed25519-history-rewrite.yml`
- `.github/workflows/one-time-owner-handoff-release-348ac750.yml`
- `.github/workflows/one-time-prod-tag-e57867b.yml`
- `.github/workflows/backend-gate.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/dashboards-build-gate.yml`
- `.github/workflows/dependency-scan.yml`
- `.github/workflows/pytest-gate.yml`
- `.nvmrc`
- `.python-version`
- `docs/engineering/WORKFLOW_EXECUTION_MAINTENANCE.md`

Forbidden: all other paths; no changes to tenant permissions, accounting, migrations, deployment targets, or enforcement thresholds.

Validation: Parse workflow YAML and run workflow policy and authoring contracts; verify PR-only cancellation expressions. Actual runner execution requires exact-head GitHub checks.

Rollback: revert this isolated PR. Restoring old credential defaults is unsafe; disable the development seed endpoint instead when rolling back its behavior.

Decision owner: repository owner. Automated checks are not independent human review. Main integration and deployed behavior are not verified by this document.
